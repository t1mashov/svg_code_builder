
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from .imports import *
from .scroll import ScrollView

from .views.base_view import BaseView

'''
Контейнеры:

1) offset - смещение дочерних на dx и dy
<offset 
    dx="5" dy="5">
    ...
</offset>

2) vector - отображение элементов друг за другом c отступом margin (dir = вертикально[v]/горизонтально[h])
<vector 
    x="10" y="5" 
    dir="h" 
    margin="10">
    ...
</vector>

3) frozen - все объекты, помещенные в frozen не имеют размера с точки зрения <vector>,
следовательно помещаются "на задний фон"
<frozen>
    ...
</frozen> 

'''

class Parser:
    def __init__(self, str_xml):
        self.str_xml = str_xml
        self.XML_VIEWS = {}
        self.elements = {}
        self.el_keys = []
        self.defattrs = {}

        self.tag_views = {
            'rect' : Rect,
            'ellipse' : Ellipse,
            'text' : TextView,
            'input' : TextArea,
            'table' : Table,
            'button' : Button,
            'ScrollView' : ScrollView
        }

    def parse_element(self, win, el:Element, dx=0, dy=0):

        ID = el.attrib.get('id', next())
        self.el_keys.append(ID)

        attrs = el.attrib.copy()
        if el.tag in ['button', 'text']:
            pos = eval(attrs.get('coords', '-1'))
        else:
            pos = eval(attrs.get('pos', '-1'))
        
        if pos == -1: pos = [dx, dy]
        else:
            x, y, *wh = pos
            pos = [x+dx, y+dy, *wh]

        pos = [int(el) for el in pos]
        
        attrs['pos'] = pos
        attrs['coords'] = pos

        attrs['win'] = win.win

        # default values
        for (k, v) in self.defattrs.items():
            if not k in attrs.keys():
                attrs[k] = v

        if el.tag in self.tag_views.keys():
            self.elements[ID] = self.tag_views[el.tag](**attrs)
        else:
            self.elements[ID] = self.XML_VIEWS[el.tag](**attrs)
        return ID
        ...

    # <offset>...</offset>
    def parse_offset(self, win, xml:Element, dx=0, dy=0):
        x = eval(xml.attrib.get('x', '0')) + dx
        y = eval(xml.attrib.get('y', '0')) + dy
        for el in xml:
            if el.tag == 'vector': 
                self.parse_vector(win, el, x, y)
            elif el.tag == 'offset':
                self.parse_offset(win, el, x, y)
            elif el.tag == 'default':
                self.defattrs = el.attrib
            elif el.tag == 'win':
                bg = eval(el.attrib.get('bg', '[230]*3'))
                win.bg = bg
            elif el.tag == 'frozen':
                self.parse_frozen(win, el, x, y)
            else:
                self.parse_element(win, el, x, y)
        return [x, y]


    # <vector dir="h">...</vector>
    def parse_vector(self, win, xml:Element, dx=0, dy=0):
        x = eval(xml.attrib.get('x', '0')) + dx
        y = eval(xml.attrib.get('y', '0')) + dy
        
        dr = xml.attrib.get('dir', 'h')
        mar = eval(xml.attrib.get('margin', '10'))

        maxes = [0, 0]
        ID = -1
        for el in xml:
            if el.tag == 'vector':

                if ID in self.elements.keys():
                # try:
                    # сдвиг главной оси на размер элемента
                    w, h = self.elements[ID].getSize()
                    if dr == 'h': x += w + mar
                    elif dr == 'v': y += h + mar
                # except: pass

                ox, oy = self.parse_vector(win, el, x, y)

                # поиск максимума из вложенных vector
                if maxes[0] < ox-x: maxes[0] = ox-x
                if maxes[1] < oy-y: maxes[1] = oy-y

                if dr == 'h': x = ox + mar
                if dr == 'v': y = oy + mar
                ID = -1
                   
        
            elif el.tag == 'offset':
                raise Exception("You can not use <offset> inside <vector>")

            elif el.tag == 'default':
                self.defattrs = el.attrib
            elif el.tag == 'win':
                bg = eval(el.attrib.get('bg', '[230]*3'))
                win.bg = bg
            elif el.tag == 'frozen':
                self.parse_frozen(win, el, x, y)
            else:
                if ID != -1:
                    if ID in self.elements.keys():
                    # try:
                        # сдвиг главной оси на размер элемента
                        w, h = self.elements[ID].getSize()
                        sx, sy = self.elements[ID].getStart()
                        if dr == 'h': x = sx + w + mar*2
                        elif dr == 'v': y = sy + h + mar*2
                    # except: pass

                ID = self.parse_element(win, el, x, y)

                if ID in self.elements.keys():
                # try:
                    w, h = self.elements[ID].getSize()
                    if w > maxes[0]: maxes[0] = w
                    if h > maxes[1]: maxes[1] = h
                # except: pass

                if dr == 'h': x += mar
                if dr == 'v': y += mar

        # сдвиг главной оси после генерации всех элементов
        if ID in self.elements.keys():
        # try:
            w, h = self.elements[ID].getSize()
            if dr == 'h': x += w + mar
            elif dr == 'v': y += h + mar
        # except: pass

        # сдвиг побочной оси при завершении парсинга vector
        if dr == 'h': y += maxes[1]
        elif dr == 'v': x += maxes[0]

        return [x, y]
    

    def parse_frozen(self, win, xml:Element, dx=0, dy=0):
        for el in xml:
            # if el.tag in ['vector', 'offset', 'fixed']:
            #     raise Exception("You cannot put the following tags in <fixed>: (<offset>, <vector>, <fixed>)")
            if el.tag == 'vector':
                print(dx, dy)
                self.parse_vector(win, el, dx, dy)
            else:
                self.parse_element(win, el, dx, dy)
        return [dx, dy]
    
            

    def get_design(self, win) -> dict:

        for view in self.XML_VIEWS.values():
            print(view.__bases__)
            if not BaseView in view.__bases__:
                raise Exception(f'{view} должен наследоваться от BaseView (ezzgui.views.base_view.BaseView)')

        root = ET.fromstring(self.str_xml)
        self.parse_offset(win, root)

        for view in self.elements.values():
            view.getStart()
            view.getSize()

        return self.elements