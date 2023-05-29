
from ezzgui.app import App
from ezzgui.imports import *

class InfoPage(App):
    '''Страница справки'''
    def __init__(self, program):
        super().__init__()
        self.base = program
        self.DESIGN = "src/xml/info_page.xml"
        self.ONCLICK = {
            'back' : [self.back, ()],
            'gens' : [self.set_theme, ('general',)],
            'coms' : [self.set_theme, ('commands',)],
            'args' : [self.set_theme, ('path_args',)],
            'lays' : [self.set_theme, ('lays',)],
        }
        self.win = program.win
        self.txt = {}
        self.load_txt()
        self.load_design()

        # отключаем редактирование поля с текстом справки
        self.VIEWS['i_info'].noreduct = True


    def back(self):
        '''Возврат на главную страницу'''
        self.win.design = self.base.VIEWS

    
    def set_theme(self, theme):
        '''Устанавливает текст справки по теме (theme)'''
        self.VIEWS['i_info'].offset = [0,0]
        self.VIEWS['i_info'].set_content(self.txt[theme])

    
    def load_txt(self):
        with open('src/about/commands.txt', encoding='utf-8') as f:
            self.txt['commands'] = f.read()
        with open('src/about/general.txt', encoding='utf-8') as f:
            self.txt["general"] = f.read()
        with open('src/about/lays.txt', encoding='utf-8') as f:
            self.txt["lays"] = f.read()
        with open('src/about/path_args.txt', encoding='utf-8') as f:
            self.txt["path_args"] = f.read()
        