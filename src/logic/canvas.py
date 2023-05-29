
import pygame
# from .const import *

from ezzgui.views.base_view import BaseView

class SVGCanvas(BaseView):
    def __init__(self, win, pos, 
            bg='[255]*3', 
            gridColor='[210]*3', 
            on_change_points=[lambda:..., ()],
            on_set_point=[lambda:..., ()], on_choose_point=[lambda:..., ()], **kwargs):
        self.win = win
        self.pos = pos
        self.color = eval(bg)
        self.grid_color = eval(gridColor)
        self.grid = {
            'active' : False,
            'level' : 15,
        }
        self.points = []
        self.point_coords = None
        self.choosen = None
        self.focused_point = None
        self.start_point = None

        self.on_change_points = on_change_points
        self.on_set_point = on_set_point
        self.on_choose_point = on_choose_point

        self.img = None

        self.active = True

        self.offset = [0, 0]
        self.shift = False
        self.ctrl = False
        self.zoom = 1
        self.zoom_img = None
        self.img_rect = pygame.Rect(0, 0, *pos[2::])
        self.on_zoom_change = None

    def detect_offset(self, events, mpos):
        if not self.on_focus(mpos): return
        z = self.zoom

        [_, _, w, h] = self.pos
        lvl = self.grid['level']
        if self.grid['active']:
            dw = ((w // z)*z) // lvl
            dh = ((h // z)*z) // lvl
            # [dw, dh] = [round(w/lvl, 2), round(h/lvl, 2)]
            if dw < 20:
                [dw, dh] = [dw*2, dh*2]
        else: 
            [dw, dh] = [20, 20]
        cngd_z = False
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 4: # up
                    if self.ctrl: 
                        self.zoom += 1
                        cngd_z = True
                    elif self.shift: self.offset[0] -= dw
                    else: self.offset[1] -= dh
                elif e.button == 5: # down
                    if self.ctrl: 
                        self.zoom -= 1
                        cngd_z = True
                    elif self.shift: self.offset[0] += dw
                    else: self.offset[1] += dh

        if self.zoom < 1:
             self.zoom = 1
             cngd_z = True
        if self.zoom > 15: 
            self.zoom = 15
            cngd_z = True

        [ox, oy] = self.offset
        if cngd_z:
            if self.on_zoom_change != None:
                self.on_zoom_change[0]( *self.on_zoom_change[1])
            dw = w // lvl
            dh = h // lvl
            self.offset[0] = (ox // dw)*dw
            self.offset[1] = (oy // dh)*dh

        [W, H] = self.pos[2::]
        zoom = self.zoom
        if ox < 0: self.offset[0] = 0
        if ox+W > W*(zoom): self.offset[0] = W*(zoom)-W
        if oy < 0: self.offset[1] = 0
        if oy+H >= H*(zoom): self.offset[1] = H*(zoom)-H
        

    def point_rel_display(self, point):
        [x, y] = point
        z = self.zoom
        [ox, oy] = self.offset
        return [
            x*z - ox,
            y*z - oy
        ]
        
    def point_rel_canvas(self, point):
        [x, y] = point
        z = self.zoom
        [ox, oy] = self.offset
        return [
            round((x + ox)/z, 2),
            round((y + oy)/z, 2)
        ]


    def updated_img(self):
        if self.img != None:
            [w, h] = self.img.get_rect().size
            z = self.zoom
            self.zoom_img = self.img

    def enable(self):
        self.active = True
    def disable(self):
        self.active = False

    def on_focus(self, mpos):
        [mx, my] = mpos
        [x, y, w, h] = self.pos
        if x <= mx <= x+w and y <= my <= y+h:
            return True
        return False
    
    def detect(self, events, mpos, mpress):
        '''Отслеживание нажатий на Canvas и -> добавление, изменение точек'''
        if not self.on_focus(mpos): 
            if mpress[0]:
                self.point_coords = None
                self.choosen = None
            return

        self.calc_point(mpos)
        self.choose_point(mpos, False)

        if not self.active: return

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.points.append(self.point_coords)
                    self.on_set_point[0]( *self.on_set_point[1])
                if e.button == 3:
                    self.choose_point(mpos)
                self.on_change_points[0]( *self.on_change_points[1])
        
        if mpress[2]:
            if self.choosen != None:
                [nx, ny] = self.point_coords
                self.points[self.choosen][0] = nx
                self.points[self.choosen][1] = ny
                self.on_change_points[0]( *self.on_change_points[1])

    
    def calc_point(self, mpos):
        '''Рассчет координат точки (по координатам мыши)'''
        [mx, my] = mpos
        [x, y, w, h] = self.pos
        if self.grid['active']:
            lvl = self.grid['level']
            dw = w // lvl
            dh = h // lvl
            self.point_coords = self.point_rel_canvas([
                round((mx - x) / dw) * dw, 
                round((my - y) / dh) * dh
            ])
        else:
            self.point_coords = self.point_rel_canvas([mx-x, my-y])
    
    def choose_point(self, mpos, choose=True):
        '''Отслеживание выбора точки (ПКМ)'''
        r = 10 # radius
        self.calc_point(mpos)
        [mx, my] = mpos
        [x, y] = [mx-self.pos[0], my-self.pos[1]]
        for i, [px, py] in enumerate(self.points):
            [px, py] = self.point_rel_display([px, py])
            if x-r < px < x+r and y-r < py < y+r:
                if choose: 
                    self.choosen = i
                    self.on_choose_point[0](*self.on_choose_point[1])
                self.focused_point = i
                return i
        self.focused_point = None
        return None

    def detect_keydown(self, keys):
        if self.choosen == None: return
        if self.choosen > len(self.points): return
        if self.choosen < 0: return
        z = self.zoom

        if keys[pygame.K_UP]:
            self.points[self.choosen][1] -= 1/z
            self.on_change_points[0]( *self.on_change_points[1])
        if keys[pygame.K_DOWN]:
            self.points[self.choosen][1] += 1/z
            self.on_change_points[0]( *self.on_change_points[1])
        if keys[pygame.K_LEFT]:
            self.points[self.choosen][0] -= 1/z
            self.on_change_points[0]( *self.on_change_points[1])
        if keys[pygame.K_RIGHT]:
            self.points[self.choosen][0] += 1/z
            self.on_change_points[0]( *self.on_change_points[1])

        [x, y, w, h] = self.pos
        [px, py] = self.points[self.choosen]
        if px > x+w: self.points[self.choosen][0] = x+w
        if px < 0: self.points[self.choosen][0] = 0
        if py > y+h: self.points[self.choosen][1] = y+h
        if py < 0: self.points[self.choosen][1] = 0

    def draw_bg(self):
        pygame.draw.rect(self.win, self.color, self.pos) # bg

    def draw(self):
        [x, y, w, h] = self.pos
        if self.grid['active']:
            lvl = self.grid['level']
            
            dw = w // lvl
            dh = h // lvl
            for i in range(lvl+1):
                pygame.draw.rect(self.win, self.grid_color, [x+i*dw, y, 1, h])
                pygame.draw.rect(self.win, self.grid_color, [x, y+dh*i, w, 1])
        
        if self.point_coords != None:
            [px, py] = self.point_coords
            [px, py] = self.point_rel_display([px, py])
            pygame.draw.circle(self.win, [180]*3, [px+x, py+y], 3)

        if self.start_point != None:
            [px, py] = self.start_point
            [px, py] = self.point_rel_display([px, py])
            if self.on_focus([px+x, py+y]):
                pygame.draw.circle(self.win, (150,250,150), [px+x, py+y], 4, 1)
        
        for [px, py] in self.points:
            [px, py] = self.point_rel_display([px, py])
            if self.on_focus([px+x, py+y]):
                pygame.draw.circle(self.win, (120,120,250), [px+x, py+y], 3)

        if self.focused_point != None and self.focused_point < len(self.points):
            [px, py] = self.points[self.focused_point]
            [px, py] = self.point_rel_display([px, py])
            pygame.draw.circle(self.win, (255,255,255), [px+x, py+y], 4)

        if self.choosen != None:
            [px, py] = self.points[self.choosen]
            [px, py] = self.point_rel_display([px, py])
            if self.on_focus([px+x, py+y]):
                pygame.draw.circle(self.win, (250,120,120), [px+x, py+y], 4)

    def spawn(self, events, mpos, mpress, keys, **kwargs):
        [x, y, _, _] = self.pos
        self.draw_bg()
        if self.zoom_img != None:
            self.win.blit(self.zoom_img, [x, y], self.img_rect)
        self.detect_offset(events, mpos)
        self.detect(events, mpos, mpress)
        self.detect_keydown(keys)
        self.draw()

        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.shift = True
        else:
            self.shift = False

        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            self.ctrl = True
        else:
            self.ctrl = False

    def getSize(self):
        return self.pos[2::]
    def getStart(self):
        return self.pos[:2:]
        