
from ezzgui.views.button import Button, BaseView
import pygame

class NiceButton(Button, BaseView):
    def __init__(self, win, coords,
                 text='', font='Arial', size='18', padding='[5, 0]', 
                 on_click_func=None, tag=None, 
                 textColor="(0,0,0)", bgColor='[150]*3', hoverColor='[200]*3',
                 borderColor="[100]*3", borderHover="[250]*3",
                 radius="9",
                 **kwargs):
        self.borderColor = eval(borderColor)
        self.borderHover = eval(borderHover)
        self.radius = eval(radius)
        super().__init__(win, coords, text, font, size, 
                         padding, on_click_func, tag, 
                         textColor, bgColor, hoverColor, **kwargs)
        
    def spawn(self, events, mpos, **kwargs):
        self.on_click_detect(events, mpos)
        r = self.radius
        if self.on_focus(mpos):
            [x, y, w, h] = self.pos
            for i, color in enumerate([self.borderHover, self.on_focus_bg_color]):
                d = i
                pygame.draw.rect(self.win, color, [x+r/2 + d, y + d, w-r - d*2, h-d*2])
                pygame.draw.rect(self.win, color, [x + d, y+r/2 + d, w - d*2, h-r - d*2])
                pygame.draw.ellipse(self.win, color, [x+d, y+d, r, r])
                pygame.draw.ellipse(self.win, color, [x+d, y+h-r-d, r, r])
                pygame.draw.ellipse(self.win, color, [x+w-r-d, y+d, r, r])
                pygame.draw.ellipse(self.win, color, [x+w-r-d, y+h-r-d, r, r])
        else:
            [x, y, w, h] = self.pos
            for i, color in enumerate([self.borderColor, self.default_bg_color]):
                d = i
                pygame.draw.rect(self.win, color, [x+r/2 + d, y + d, w-r - d*2, h-d*2])
                pygame.draw.rect(self.win, color, [x + d, y+r/2 + d, w - d*2, h-r - d*2])
                pygame.draw.ellipse(self.win, color, [x+d, y+d, r, r])
                pygame.draw.ellipse(self.win, color, [x+d, y+h-r-d, r, r])
                pygame.draw.ellipse(self.win, color, [x+w-r-d, y+d, r, r])
                pygame.draw.ellipse(self.win, color, [x+w-r-d, y+h-r-d, r, r])
        [x, y, _, _] = self.pos
        self.win.blit(self.text.picture, (x+self.pd[0], y+self.pd[1]))
    