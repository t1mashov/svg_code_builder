
from ezzgui.app import App
from ezzgui.imports import *

from tkinter import Tk
from tkinter.filedialog import asksaveasfilename

from .logic.canvas import SVGCanvas
from .logic.svgcodebuilder import SVGCodeBuilder

from .info import InfoPage

class Program(App):
    '''Главный класс приложения'''
    def __init__(self):
        super().__init__()
        # self.WIN_SIZE = (850,500)
        self.WIN_SIZE = (850,500)
        self.DESIGN = "src/xml/main_page.xml"
        self.XML_VIES = {
            'SVGCanvas' : SVGCanvas
        }

        # связи кнопок и их функций
        self.ONCLICK = {
            'com_M' : [self.add_command, ('M',)],
            'com_L' : [self.add_command, ('L',)],
            'com_Z' : [self.add_command, ('Z',)],
            'com_C' : [self.add_command, ('C',)],
            'com_S' : [self.add_command, ('S',)],
            'com_Q' : [self.add_command, ('Q',)],
            'com_T' : [self.add_command, ('T',)],
            'com_A' : [self.add_command, ('A',)],

            'add_path' : [self.path_control, ('add path',)],
            'path_up' : [self.path_control, ('path /\\',)],
            'move_up' : [self.path_control, ('move /\\',)],
            'path_down' : [self.path_control, ('path \\/',)],
            'move_down' : [self.path_control, ('move \\/',)],
            'delete' : [self.path_control, ('delete',)],
            'grid_apply' : [self.grid_apply, ()],
            'move_all' : [self.moveall, ()],
            'save' : [self.save, ()],
            'com_up' : [self.command_up_down, ("command /\\",)],
            'com_down' : [self.command_up_down, ("command \\/",)],

            'info' : [self.to_info_page, ()],
        }

    def design_settings(self):
        self.VIEWS['i_d_args'].tab_len = 2
        self.VIEWS['i_grid'].one_row = True
        self.VIEWS['i_path_name'].one_row = True

        self.VIEWS['i_pathes'].set_content('Main')
        self.VIEWS['i_pathes'].noreduct = True
        self.VIEWS['i_pathes'].selection.poses = [(0,0), (20,0)]
        self.VIEWS['i_pathes'].selection.s_rows = self.VIEWS['i_pathes'].selection.selected_rows()

    
    def on_create(self):
        # страница "Справка"
        self.info_page:InfoPage = InfoPage(self)

        super().load_design()
        self.design_settings()

        self.cnv:SVGCanvas = self.VIEWS['canvas']
        self.cnv.on_zoom_change = [self.set_cell_size, ()]
        self.code_builder:SVGCodeBuilder = SVGCodeBuilder(self.cnv, self.VIEWS['i_d_args'], self.VIEWS['i_path_args'])
        
    # переход на страницу справки
    def to_info_page(self):
        self.win.design = self.info_page.VIEWS
        

    # вычислить и установить размер сетки
    def set_cell_size(self):
        txt = ''
        if self.cnv.grid['active']:
            lvl = self.cnv.grid['level']
            z = self.cnv.zoom
            txt = f'1 cell = {round((300/z) / lvl, 2)}px'
        self.VIEWS['t_cell_size'].text.text = txt
        self.VIEWS['t_cell_size'].text.render()
    
    # добавление команды
    def add_command(self, comm):
        self.VIEWS['t_cur_command'].text.text = comm
        self.VIEWS['t_cur_command'].text.render()
        self.code_builder.add_func(comm)
    
    # нажатие на кнопки
    def command_up_down(self, btxt):
        self.code_builder.command_up_down(btxt)
        c = self.code_builder.current
        try:
            self.VIEWS['t_cur_command'].text.text = self.code_builder.container[c['path']]['d'][c['func']]['func']
            self.VIEWS['t_cur_command'].text.render()
        except: ...
    
    # кнопки управления слоями
    def path_control(self, btxt):
        name = 'Path'
        if btxt == 'add path':
            name = self.VIEWS['i_path_name'].get_text()
            self.VIEWS['i_path_name'].set_content('')

        self.code_builder.path_controllers(btxt, name)
        c = self.code_builder.current
        path_names = [path['name'] for path in self.code_builder.container]
        self.VIEWS['i_pathes'].set_content('\n'.join(path_names))
        
        [(x1, y1), (x2, y2)] = self.VIEWS['i_pathes'].selection.poses
        y1 = c['path']
        y2 = c['path']
        self.VIEWS['i_pathes'].selection.poses = [(x1, y1), (x2, y2)]
        self.VIEWS['i_pathes'].selection.s_rows = self.VIEWS['i_pathes'].selection.selected_rows()
        if self.code_builder.indexes_current_test() != {'path':True, 'func':True}: 
            return
        self.VIEWS['t_cur_command'].text.text = self.code_builder.container[c['path']]['d'][c['func']]['func']
        self.VIEWS['t_cur_command'].text.render()
        
    # сохранение картинки
    def save(self):
        size = self.VIEWS['i_img_size'].get_text()
        try:
            if size != '':
                size = [float(el) for el in size.split('x')]
            else:
                size = [0, 0]
        except: return
        root = Tk()
        root.withdraw()
        file_path = asksaveasfilename(
            initialfile='result.svg',
            filetypes=(('SVG files', '*.svg'), ('All files', '*.*'))
        )
        if not '.svg' in file_path:
            file_path += '.svg'
        txt = self.code_builder.collect_svg(save=True, size=size)
        if file_path.strip() == '.svg': return

        print(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(txt)
        root.destroy()

    # изменение всех точек слоя
    def moveall(self):
        try:
            args = self.VIEWS['i_move_all'].get_text().split(';')
            op1 = args[0][0]
            dx = float(args[0][1::])
            op2 = args[1][0]
            dy = float(args[1][1::])
            self.code_builder.moveall(op1, dx, op2, dy)
        except:
            print('incorrect moveall args')


    # установить сетку
    def grid_apply(self):
        src = self.VIEWS['i_grid'].get_text()
        try:
            num = int(src)
            if num < 3: num = 3
            if num > 30: num = 30
            self.cnv.grid['active'] = True
            self.cnv.grid['level'] = num
            self.VIEWS['i_grid'].set_content(f'{num}')
        except:
            self.cnv.grid['active'] = False
            self.cnv.grid['level'] = 15
            self.VIEWS['i_grid'].set_content('')
        
        self.set_cell_size()

    