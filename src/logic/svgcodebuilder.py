
from svg import Parser, Rasterizer, SVG
from PIL import Image

import io
import pygame

from ezzgui.views.textarea import TextArea
from .canvas import SVGCanvas

import re
import os

'''

container = [
    {
        'name' : 'Base',
        'args' : 'fill="#5f5" stroke="#000"',
        'd': [
            {func:'L', lines:[
                {arg:'', points:[(45,22)]}
            ]},
            {func:'Q', lines:[
                {arg:'', points:[(10,3), (13,42)]}
            ]},
            {func:'A', lines:[
                {arg:'1,1 45 0 0', points:[(45,22)]},
                {arg:'2,3 45 0 1', points:[(54,23)]}
            ]},
            {func:'Z', lines:[]}
        ]
    },
]

'''

def num(x):
    try:
        x = float(x)
        if int(x) == x:
            return int(x)
        else: return round(x, 3)
    except: return 0

def pcl(comm):
    if comm in 'VvHh': return 0
    if comm in 'AaMmLlTtZz': return 1
    if comm in 'QqSs': return 2
    if comm in 'Cc': return 3

class SVGCodeBuilder:
    def __init__(self, cnv:SVGCanvas, d:TextArea, path:TextArea):
        self.cnv = cnv
        self.d = d
        self.path = path
        self.cnv.on_change_points = [self.update_by_canvas, ()]
        self.cnv.on_choose_point = [self.find_point, ()]
        self.container = [
            {
                'name':'Main', 'args':'',
                'd' : [
                    {'func':'M', 'lines':[{'arg':'', 'points':[(150,150)]}]}
                ]
            }
        ]
        self.current = {
            'path' : 0,
            'func' : 0,
        }

        self.d.on_text_change = [self.update_d_by_text, ()]
        self.path.on_text_change = [self.update_path, ()]

        self.d.set_content(self.collect_d())
        self.cnv.points = self.collect_points()


    def print_container(self):
        os.system('cls')
        tab = 0
        for path in self.container:
            print('name :', path['name'])
            print('args :', path['args'])
            print('d : [')
            tab += 1
            for func in path['d']:
                print(f'{"  "*tab}func : "{func["func"]}"')
                print(f'{"  "*tab}lines : [')
                tab += 1
                for line in func['lines']:
                    print(f'{"  "*tab}{line}')
                tab -= 1
                print(f'{"  "*tab}]')
            tab -= 1
            print(f'{"  "*tab}]')
        print('}')


    def load_svg(self):
        try:
            svg = Parser.parse_file('./src/res/temp.svg')
            rast = Rasterizer()
            buff = rast.rasterize(svg, svg.width, svg.height)
            im = Image.frombytes('RGBA', (svg.width, svg.height), buff)
            im.save('./src/res/temp.png')
        except: ...
        
        self.cnv.img = pygame.image.load('./src/res/temp.png')
        self.cnv.updated_img()

    def fill_file(self):
        txt = self.collect_svg()
        file = open('./src/res/temp.svg', 'w', encoding='utf-8')
        file.write(txt)
        file.close()
        self.load_svg()


    def update_by_canvas(self):
        c = self.current
        if c['func']==-1: return

        cps = self.cnv.points

        lines = self.container[c['path']]['d'][c['func']]['lines']
        comm = self.container[c['path']]['d'][c['func']]['func']
        args = [line['arg'] for line in lines]
        
        arg_idx = 0 if len(args) > 0 else None
        lines.clear()
        for point in cps:
            point = [num(el) for el in point]
            if len(lines) == 0 or len(lines[-1]['points']) >= pcl(comm):
                lines.append({
                    'arg': args[arg_idx] if arg_idx != None and arg_idx < len(args) else 
                           ('1,1 0 0 0' if comm in 'Aa' else 
                            '0' if comm in 'VvHh' else ''),
                    'points': [point]
                })
                if arg_idx != None: arg_idx += 1
            else:
                lines[-1]['points'].append(point)
        self.d.set_content(self.collect_d())
        self.set_start_point()
        self.fill_file()


    def update_d_by_text(self):
        c = self.current
        try:
            self.container[c['path']]['d'] = self.parse_d()
        except: 
            print('<syntax error>')
            return
        try:
            self.set_start_point()
        except:
            print('<set_start_point error>')
        d = self.container[c['path']]['d']
        if len(d) == 0:
            self.current['func'] = -1
        else:
            if self.current['func'] > len(self.container[c['path']]['d'])-1:
                self.current['func'] = len(self.container[c['path']]['d'])-1
            self.cnv.points = self.collect_points()
        self.set_start_point()
        self.fill_file()
        

    # собирает точки из линий текущей функции в 1 массив
    # для обновления canvas из ta
    def collect_points(self):
        c = self.current
        if self.indexes_current_test() != {'path':True, 'func':True}:
            return []

        lines = self.container[c['path']]['d'][c['func']]['lines']
        res = []
        for line in lines:
            res += [*[list(point) for point in line['points']]]
        # print('<collect_points>', res)
        return res

    def set_start_point(self):
        c = self.current
        if (self.current['func'] > 0 and 
            len(self.container[c['path']]['d'][c['func']-1]['lines']) > 0 and
            len(self.container[c['path']]['d'][c['func']-1]['lines'][-1]['points']) > 0):
            self.cnv.start_point = self.container[c['path']]['d'][c['func']-1]['lines'][-1]['points'][-1]
        else:
            self.cnv.start_point = None

    def indexes_current_test(self):
        res = {'path':True, 'func':True}
        c = self.current
        cont = self.container
        if c['path'] >= len(cont) or c['path']<0: res['path'] = False
        if c['func'] >= len(cont[c['path']]['d']) or c['func']<0: res['func'] = False
        return res

    # вызывать при нажатии кнопок с функциями
    def add_func(self, comm):
        c = self.current
        self.update_d_by_text()
        if (c['func'] == -1 or 
                len(self.container[c['path']]['d'][c['func']]['lines']) != 0 or 
                self.container[c['path']]['d'][c['func']]['func'] in 'Zz'):
            # self.container[c['path']]['d'].append({
            #     'func' : comm,
            #     'lines' : []
            # })
            self.container[c['path']]['d'].insert(c['func']+1, {
                'func' : comm,
                'lines' : []
            })
            # self.current['func'] = len(self.container[c['path']]['d'])-1
            self.current['func'] += 1

            self.cnv.points.clear()
            self.set_start_point()
        else:
            self.container[c['path']]['d'][c['func']]['func'] = comm
        self.update_by_canvas()
        self.find_func()
        

    def parse_d(self):
        txt = self.d.get_text()
        txt = re.sub('[ :,\n]', ' ', txt)
        txt = re.sub('[ ]+', ' ', txt).strip()
        if txt == '': return []
        tmp = ''
        for c in txt:
            if not c in '-1234567890. ': tmp += f';{c};'
            else: tmp += c
        mas = list(filter(
            bool, 
            [el.strip() for el in tmp.split(';')]
        ))
        tmp = []
        i = 0
        while i < len(mas):
            if mas[i] in 'Zz':
                tmp += [[mas[i]]]
            else:
                if i+1 < len(mas):
                    tmp += [[mas[i], mas[i+1]]]
                    i += 1
            i += 1

        mas = tmp
        res = []
        for el in mas:
            # el = ['L', '15 34']
            dct = {}
            lines = []
            dct['func'] = el[0]
            if el[0] in 'Zz': # 0 points
                ...
            
            elif el[0] in 'MmLlTtQqSsCc':
                l = 1
                if el[0] in 'MmLlTt': l = 2
                elif el[0] in 'QqSs': l = 4
                elif el[0] in 'Cc': l = 6
                arr = [num(el) for el in el[1].split(' ')]
                groups = [arr[i*l:(i+1)*l:] for i in range(len(arr)//l)]
                for line in groups:
                    lines += [
                        {'arg':'', 'points':[
                            (line[i], line[i+1]) for i in range(len(line))[::2]
                        ]}
                    ]
            
            elif el[0] in 'Aa':
                l = 7
                arr = [num(el) for el in el[1].split(' ')]
                groups = [arr[i*l:(i+1)*l:] for i in range(len(arr)//l)]
                for line in groups:
                    lines += [
                        {'arg':' '.join([str(n) for n in line[:5:]]), 
                         'points':[tuple(line[5::])]}
                    ]

            # -- new --
            elif el[0] in 'VvHh':
                l = 1
                arr = [num(el) for el in el[1].split(' ')]
                groups = [arr[i:(i+1):] for i in range(len(arr))]
                for line in groups:
                    lines += [
                        {'arg':f'{line[0]}', 
                         'points':''}
                    ]
            
            dct['lines'] = lines
            res.append(dct)
        return res


    def update_path(self):
        c = self.current
        self.container[c['path']]['args'] = self.parse_path()
        self.fill_file()

    def collect_path(self):
        c = self.current
        return self.container[c['path']]['args']

    def parse_path(self):
        txt = self.path.get_text()
        txt = re.sub(r'[ ]+', ' ', txt)
        return txt

    # собирает из path (container[?]) текст для self.d (TextArea)
    def collect_d(self, idx=None, zoom=False):
        z = self.cnv.zoom
        p = ''
        path = self.container[self.current['path'] if idx==None else idx]
        for el in path['d']:
            p += el['func']+' '
            if el['func'] in 'zZ': p += '\n'
            for i in range(len(el['lines'])):
                line = el['lines'][i]
                p += line['arg']+' ' if line['arg']!='' else ''
                p += ' '.join([f'{ln[0]*z},{ln[1]*z}' if zoom else f'{ln[0]},{ln[1]}' 
                               for ln in line['points']])+'\n'
                if i != len(el['lines'])-1:
                    p += '  '
        return p
        
    def collect_svg(self, save=False, size=[0,0]):
        if size == [0,0]: size = self.cnv.pos[2::]
        w, h = size
        z = self.cnv.zoom
        [ox, oy] = self.cnv.offset
        svg = f'''<svg 
xmlns="http://www.w3.org/2000/svg" 
    width="{w}" 
    height="{h}" 
    {'' if save else f'viewBox="{round(ox/z, 2)} {round(oy/z, 2)} {round(self.cnv.pos[2]/z, 2)} {round(self.cnv.pos[3]/z, 2)}"'} 
    style="">
<rect id="backgroundrect" width="100%" height="100%" x="0" y="0" fill="none" stroke="none"/>
'''
        for i, path in enumerate(self.container):
            p = '<path '
            p += path['args']+' '
            p += 'd="'
            p += self.collect_d(i)
            p += '"/>'
            svg += p+'\n'
        svg += '</svg>'
        return svg

    
    def command_up_down(self, btxt):
        c = self.current
        if btxt == 'command /\\':
            if c['func'] > 0:
                self.current['func'] -= 1
                self.cnv.points = self.collect_points()
            self.find_func()
        elif btxt == 'command \\/':
            if c['func'] < len(self.container[c['path']]['d'])-1:
                self.current['func'] += 1
                self.cnv.points = self.collect_points()
            self.find_func()
        self.set_start_point()

    def path_controllers(self, btxt, name="Path"):
        c = self.current
        if btxt in ['path /\\', 'path \\/']:
            if btxt == 'path /\\':
                if c['path'] > 0:
                    self.current['path'] -= 1
            if btxt == 'path \\/':
                if c['path'] < len(self.container)-1:
                    self.current['path'] += 1
            if len(self.container[c['path']]['d']) > 0:
                self.current['func'] = len(self.container[c['path']]['d']) - 1
            else:
                self.current['func'] = -1
        if btxt == 'add path':
            self.container.append({
                'name': name, 
                'args': '',
                'd' : [
                    {'func':'M', 'lines':[{'arg':'', 'points':[(150,150)]}]}
                ]
            })
            self.current['func'] = 0
            self.current['path'] = len(self.container)-1
        if btxt == 'delete':
            if len(self.container) > 1:
                del self.container[c['path']]
                self.current['path'] -= 1
                self.current['func'] = len(self.container[c['path']]['d']) - 1
            if self.current['path'] < 0: self.current['path'] = 0
            if self.current['path'] > len(self.container)-1:
                self.current['path'] = len(self.container)-1
            

        if btxt == 'move /\\':
            if c['path'] > 0:
                self.container[c['path']], self.container[c['path']-1] = \
                    self.container[c['path']-1], self.container[c['path']]
                self.path_controllers('path /\\')

        if btxt == 'move \\/':
            if c['path'] < len(self.container)-1:
                self.container[c['path']], self.container[c['path']+1] = \
                    self.container[c['path']+1], self.container[c['path']]
                self.path_controllers('path \\/')
        
        self.d.set_content(self.collect_d())
        self.path.set_content(self.collect_path())
        self.cnv.points = self.collect_points()
        self.update_by_canvas()

    
    def moveall(self, op1, dx, op2, dy):
        def cng(a, op, b):
            return eval(f'{a}{op}{b}')
        c = self.current
        cont = self.container
        if c['path'] > len(self.container)-1: return
        for di, d in enumerate(cont[c['path']]['d']):
            for li, line in enumerate(d['lines']):
                for pi, p in enumerate(line['points']):
                    (x, y) = p
                    p = (cng(x, op1, dx), cng(y, op2, dy))
                    self.container[c['path']]['d'][di]['lines'][li]['points'][pi] = p

                # изменение аргументов <A>, если оператор == '*' или '/'
                if d['func'] in 'Aa' and (op1 in '*/') and (op2 in '*/'):
                    args = [num(el) for el in line['arg'].replace(',', ' ').split()]
                    rx, ry = args[:2:]
                    rx = cng(rx, op1, dx)
                    ry = cng(ry, op2, dy)
                    args[0:2:] = [rx, ry]
                    args = ' '.join([str(el) for el in args])
                    self.container[c['path']]['d'][di]['lines'][li]['arg'] = args

        self.d.set_content(self.collect_d())
        self.update_d_by_text()
        self.update_by_canvas()


    def find_func(self):
        c = self.current
        y = 0
        for f in self.container[c['path']]['d'][:c['func']:]:
            y += len(f['lines'])
            if len(f['lines']) == 0:
                y += 1
        self.d.selection.poses = [(0, y), (1, y)]
        self.d.selection.s_rows = self.d.selection.selected_rows()
        

    def find_point(self):
        try:
            c = self.current
            z = self.cnv.zoom
            pidx = self.cnv.choosen
            lidx = pidx // pcl(self.container[c['path']]['d'][c['func']]['func'])
            y = 0
            for f in self.container[c['path']]['d'][:c['func']:]:
                y += len(f['lines'])
                if len(f['lines']) == 0:
                    y += 1
            y += lidx
            s = 'X '
            x = 2 # min x = 2
            line = self.container[c['path']]['d'][c['func']]['lines'][lidx]
            x += len(line['arg'])+1 if line['arg'] != '' else 0
            pidx = pidx % pcl(self.container[c['path']]['d'][c['func']]['func'])
            for p in line['points'][:pidx:]:
                x += len(f'{p[0]},{p[1]} ')
            x2 = x + len(f'{line["points"][pidx][0]},{line["points"][pidx][1]}')
            self.d.selection.poses = [(x, y), (x2-1, y)]
            self.d.selection.s_rows = self.d.selection.selected_rows()
        except:
            print('<ERROR> Some error in find_point()')
        
