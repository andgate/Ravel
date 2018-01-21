from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.bubble import Bubble
from kivy.gesture import Gesture, GestureDatabase
from kivy.graphics import Color, Ellipse, Line, Triangle, Rotate, PushMatrix, PopMatrix
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.properties import ListProperty, ObjectProperty
from functools import partial
from math import atan2, cos, sin, fabs, degrees, radians, pi



class ArrowWidget(Widget):
    head_height = 8
    
    obj_a = None
    obj_b = None

    def __init__(self, **kwargs):
        super(ArrowWidget, self).__init__(**kwargs)
        with self.canvas:
            Color(1,0,0)
            self.tail = Line(points=[], width=1.3)
            PushMatrix()
            self.rot = Rotate(angle=0)
            self.head = Triangle(points=[])
            PopMatrix()

    def update_line(self, *args, **kwargs):
        if self.obj_a is not None and self.obj_b is not None:
            if hasattr(self.obj_a, 'center_x') and hasattr(self.obj_a, 'center_y')  and hasattr(self.obj_a, 'height') and hasattr(self.obj_b, 'center_x') and hasattr(self.obj_b, 'center_y')and hasattr(self.obj_b, 'height'):
                a_r = self.obj_a.height/2.0
                a_x1 = self.obj_a.center_x
                a_y1 = self.obj_a.center_y

                b_r = self.obj_b.height/2.0
                b_x1 = self.obj_b.center_x
                b_y1 = self.obj_b.center_y
                
                a_theta = atan2(b_y1-a_y1, b_x1-a_x1)
                b_theta = atan2(a_y1-b_y1, a_x1-b_x1)
                
                a_x2 = a_x1 + (a_r * cos(a_theta))
                a_y2 = a_y1 + (a_r * sin(a_theta))

                b_x2 = b_x1 + (b_r * cos(b_theta))
                b_y2 = b_y1 + (b_r * sin(b_theta))
                
                self.tail.points = [a_x2, a_y2, b_x2, b_y2]

                head_height = self.head_height
                head_base = head_height * 2

                head_x1 = b_x2
                head_y1 = b_y2

                head_x2 = head_x1 - head_height
                head_y2 = head_y1 + head_height

                head_x3 = head_x1 - head_height
                head_y3 = head_y1 - head_height
                
                self.rot.angle  = degrees(a_theta)
                self.rot.origin = (head_x1, head_y1)
                self.rot.axis   = (0, 0, 1)
                self.head.points = [head_x1, head_y1, head_x2, head_y2, head_x3, head_y3]
                self.canvas.ask_update()
        

    def set_obj_a(self, obj):
        if hasattr(obj, 'pos'):
            self.obj_a = obj
            self.obj_a.bind(pos=self.update_line)
            self.update_line()

    def set_obj_b(self, obj):
        if hasattr(obj, 'pos'):
            self.obj_b = obj
            self.obj_b.bind(pos=self.update_line)
            self.update_line()



class MapWidget(Widget):
    pass


class ObjectWidget(Widget):
    def place_obj(self, x, y):
        self.x = x - self.width / 2
        self.y = y - self.height / 2



class WorldWidget(Widget):
    obj_held = None
    spawn_event = None

    def on_touch_move(self, touch):
        if self.obj_held is not None:
            self.obj_held.place_obj(touch.x, touch.y)


    def on_touch_down(self, touch):
        if touch.is_double_tap:
            obj = self.pick(*touch.pos)
            if obj is not None:
                if self.obj_held is not obj:
                    self.grab(obj)
                    return True
                return False
            else:
                self.spawn_object(touch)
                return False

    def on_touch_up(self, touch):
        if self.obj_held:
            self.drop()

#    def create_spawn_clock(self, touch):
#        callback = partial(self.spawn_object, touch)
#        self.spawn_event = Clock.schedule_once(callback, .5)

#    def delete_spawn_clock(self, touch):
#        if self.spawn_event is not None:
#            self.spawn_event.cancel()
#            self.spawn_event = None

#    def spawn_object(self, touch, *args):

    def spawn_object(self, touch):
        obj = ObjectWidget()
        obj.place_obj(touch.x, touch.y)
        self.add_widget(obj)


    def del_object(self, obj):
        self.remove_widget(obj)


    def grab(self, obj):
        self.obj_held = obj

    def drop(self):
        self.obj_held = None

    def pick(self, x, y):
        for obj in self.children:
            if obj.collide_point(x, y):
                return obj
        return None


class PencilWidget(Widget):
    pencil_line = None

    def draw_start(self, touch):
        self.canvas.clear()
        with self.canvas:
            Color(1,1,1)
            self.pencil_line = Line(points=(touch.x, touch.y), width=1.5)

    def draw(self, touch):
        self.pencil_line.points += [touch.x, touch.y]



class StudioWidget(Widget):
    pencil = None

    def on_touch_down(self, touch):
        if not touch.is_double_tap:
            self.start_pencil(touch)
            touch.arrow = ArrowWidget()
            touch.arrow.set_obj_a(self.ids.world.pick(touch.x, touch.y))
        return super(StudioWidget, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        self.apply_pencil(touch)
        obj = self.ids.world.pick(*touch.pos)

        if hasattr(touch, 'arrow'):
            arr = touch.arrow
            if arr.obj_a is None:
                arr.set_obj_a(obj)
            elif hasattr(arr.obj_a, 'pos') and hasattr(obj, 'pos'):
                if arr.obj_a.pos != obj.pos and arr.obj_b is None:
                    arr.set_obj_b(obj)
                    self.ids.map.add_widget(arr)
                    self.stop_pencil()
            
        return super(StudioWidget, self).on_touch_move(touch)
    

    def on_touch_up(self, touch):
        self.stop_pencil()
        # if obj_a, then make new object b, and arrow from a to b
        # Later on, the arrow chosen will determine the object produced
        # This may be animated
        return super(StudioWidget, self).on_touch_up(touch)


    def start_pencil(self, touch):
        self.pencil = PencilWidget()
        self.pencil.draw_start(touch)
        self.add_widget(self.pencil)

    def apply_pencil(self, touch):
        if self.pencil is not None:
            self.pencil.draw(touch)

    def stop_pencil(self):
        if self.pencil is not None:
            self.remove_widget(self.pencil)
        self.pencil = None
        self.obj_a = None
        self.obj_b = None



class RootWidget(BoxLayout):
    pass


class RavelApp(App):
    
    def build(self):
        return RootWidget()


if __name__ == '__main__':
    RavelApp().run()
