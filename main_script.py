import logging
import os, sys
from re import search, sub, findall
from inspect import getframeinfo, stack

class Logger():
    def __init__(self):
        main_path=os.path.dirname(stack()[1][1]).replace("\\", "/")+"/"
        logging.basicConfig(filename=main_path+"logs/latest.log",filemode='w',level=logging.DEBUG,force=True)

class DynamicObject():
    """A class made to store Dynamic objects in an easy way."""
    uid=None
    object_class=None
    nickname=None
    custom_pos=None
    custom_size=None
    updated=False
    offset_pos=None
    def __init__(self,this_object,current_canvas,current_window=None,nickname=None,proportions=None,custom_size=None,custom_pos=None,offset_pos=None,on_touch=None,object_dict=None,link_with_existing=False):
        """:param this_object: a kivy.graphics object
        :param current_canvas: the widget in which the object is
        :param current_window: the window in which the object is; is only used for updating the space when an object is linked to an already existing DynamicObject, so when link_with_existing is set to True
        :param str nickname: a name to recognize this object; if not set, is equal to the object's uid
        :param tuple custom_size: a tuple of two functions which define the object's size when the update_space() method is called. Both can be set as None. For more info about functions, see translate_function()
        :param tuple custom_pos: a tuple of two functions which define the object's pos when the update_space() method is called. Both can be set as None. For more info about functions, see translate_function()
        :param proportions: proportions by which the object is downscaled in the format "n:n"
        :param on_touch: a dictionary which says which functions to call if the object is touched in a certain way. Here's an example: {"left":{"call":"a_function()"}}. In order to mention the current object, use "dynamicobject" or "<self>"
        :param object_dict: a dictionary which stores various data about the non-graphical object
        :param link_with_existing: a bool which determines if a brand new object should be created or instead if it should be linked to an already existing object in the list with the same nickname
        """
        normal_init=True
        if link_with_existing and nickname!=None:
            existing_object=self.get_object_class(current_canvas,nickname=nickname)
            if existing_object!=None:
                existing_object.object_class=this_object
                current_canvas.canvas.add(this_object)
                existing_object.update_space(current_canvas,current_window)
                existing_object.updated=False
                normal_init=False
            else:
                normal_init=True
        else:
            normal_init=True
        if normal_init:
            self.uid=this_object.uid
            self.object_class=this_object
            self.nickname=nickname if nickname!=None else this_object.uid
            self.proportions=proportions if proportions!=None else None
            self.custom_pos=custom_pos if custom_pos!=None else None
            self.offset_pos=offset_pos if offset_pos!=None else (None,None)
            self.custom_size=custom_size if custom_size!=None else None
            self.on_touch=on_touch if on_touch!=None else None
            self.object_dict=object_dict if object_dict!=None else None
            current_canvas.objects_list.append(self)
    
    def update_space(self,current_canvas,current_window):
        """Does whatever is needed in order to update an object's spatial properties"""
        if not self.updated:
            self.update_size(current_canvas,current_window)
            self.update_pos(current_canvas,current_window)
            d_print("Space updated for object %s; size(%i,%i); pos(%i,%i)"%(self.nickname,self.object_class.size[0],self.object_class.size[1],self.object_class.pos[0],self.object_class.pos[1]))
        self.updated=True
    def update_size(self,current_canvas,current_window):
        """Updates object size depending on its properties"""
        size_x=self.object_class.size[0]
        size_y=self.object_class.size[1]
        
        #Determine custom size
        if self.custom_size!=None:
            if self.custom_size[0]!=None:
                size_x=eval(translate_function(self.custom_size[0], axis=0))
            if self.custom_size[1]!=None:
                size_y=eval(translate_function(self.custom_size[1], axis=1))
        #Reduce size according to proportions
        if self.proportions!=None:
            prop_size=convert_proportion_string(self.proportions,size_x,size_y)
            size_x=prop_size[0]
            size_y=prop_size[1]
        self.object_class.size=(size_x,size_y)
    def update_pos(self,current_canvas,current_window):
        pos_x=self.object_class.pos[0]
        pos_y=self.object_class.pos[1]

        if self.custom_pos!=None:
            if self.custom_pos[0]!=None:
                self.custom_pos=(translate_function(self.custom_pos[0],axis=0),self.custom_pos[1])
                pos_x=eval(self.custom_pos[0])
            if self.custom_pos[1]!=None:
                self.custom_pos=(self.custom_pos[0],translate_function(self.custom_pos[1],axis=1))
                pos_y=eval(self.custom_pos[1])
        if self.offset_pos!=None:
            if self.offset_pos[0]!=None:
                pos_x=pos_x+eval(translate_function(self.offset_pos[0],axis=0))
            if self.offset_pos[1]!=None:
                pos_y=pos_y+eval(translate_function(self.offset_pos[1],axis=1))

        self.object_class.pos=(pos_x,pos_y)

    def was_touched(self,touch):
        """Returns a bool which tells if this object has been touched"""
        if self.on_touch!=None:
            if touch.button in self.on_touch:
                if str(type(self.object_class))=="<class 'kivy.graphics.vertex_instructions.Ellipse'>":
                    #FIXME: not working with angled shapes
                    this_center=(self.object_class.pos[0]+(self.object_class.size[0]/2),self.object_class.pos[1]+(self.object_class.size[1]/2))
                    if ((touch.pos[0]-this_center[0])**2)/((self.object_class.size[0]/2)**2)+((touch.pos[1]-this_center[1])**2)/((self.object_class.size[1]/2)**2) <= 1: #Reference matematica: https://math.stackexchange.com/questions/76457/check-if-a-point-is-within-an-ellipse
                        return True
                    else:
                        return False
                elif str(type(self.object_class))=="<class 'kivy.graphics.vertex_instructions.Rectangle'>":
                    #FIXME: not working with angled shapes
                    if (self.object_class.pos[0]<=touch.pos[0] and self.object_class.pos[1]<=touch.pos[1]) and (self.object_class.size[0]+self.object_class.pos[0]>=touch.pos[0] and self.object_class.size[1]+self.object_class.pos[1]>=touch.pos[1]):
                        return True
                    else:
                        return False
            else:
                return False
        else:
            return False
    def touch_function(self,touch):
        """Outputs an eventual touch function for the touched object"""
        output_value="d_print('Empty touch function')"
        if self.on_touch!=None:
            if touch.button in self.on_touch:
                output_value=self.on_touch[touch.button]["call"].replace("<self>","dynamicobject")
        return output_value

    def get_object_ind_by_name(self,name,current_canvas):
        """Get an object's index in a canvas' objects_list searching by its name. If no match is found, the returned value is -1"""
        output_value=-1
        i=0
        for oggetto in current_canvas.objects_list:
            if oggetto.nickname==name:
                output_value=i
            i+=1
        return output_value
    def get_object_class(self,current_canvas,current_window=None,nickname=None,space_update=False):
        """Returns an object class, found by using the given parameters"""
        output_value=None
        if nickname!=None:
            output_value=current_canvas.objects_list[self.get_object_ind_by_name(nickname,current_canvas)]
        if space_update:
            output_value.update_space(current_canvas,current_window)
        return output_value

    def remove_object(self,current_canvas,nickname=None,delete_from_list=False):
        """Removes an object from the canvas. If delete_from_list is set as True, the object will be also removed from Widget.objects_list, leading to potential errors. If not removed, objects can later be re-linked, gaining the same properties as the actual class, but having a different kivy base object."""
        if nickname!=None:
            this_object=self.get_object_class(current_canvas,nickname=nickname)
        else:
            this_object=self
        current_canvas.canvas.remove(this_object.object_class)
        if delete_from_list:
            current_canvas.objects_list.remove(self)

def convert_numeric_string(numeric_string:str,total_amount=0):
    """Converts a numeric string to a normal number.
    
    Inputting a fraction in the format '1/2f' will return the total amount divided by that number"""
    output_amount=0
    fractional_values=search("(\d*)/(\d*)f",numeric_string)
    if fractional_values!=None:
        output_amount=(total_amount*int(fractional_values.group(1)))/int(fractional_values.group(2))
    return output_amount
def convert_proportion_string(proportion_string:str,base_x,base_y):
    """Proportionates values"""
    output_amount=(0,0)
    re_search=search("(\d*)\:(\d*)",proportion_string)
    if re_search!=None:
        proportion_x=int(re_search.group(1))
        proportion_y=int(re_search.group(2))

        #If the coefficient isn't perfect, a different and proportionate size is outputted
        if (base_x*proportion_y)/proportion_x<base_y:
            output_amount=(base_x,(base_x*proportion_y)/proportion_x)
        elif (base_y*proportion_x)/proportion_y<base_x:
            output_amount=((base_y*proportion_x)/proportion_y,base_y)
        else:
            output_amount=(base_x,base_y)
    return output_amount

def d_print(stringa):
    """A simple tool for debug printing"""
    caller=getframeinfo(stack()[1][0])
    logging.debug(" [%s][%s] %s"%(caller.function,caller.lineno,stringa))
def w_print(stringa):
    caller=getframeinfo(stack()[1][0])
    logging.warning(" [%s][%s] %s"%(caller.function,caller.lineno,stringa))

def translate_function(this_function,axis=0):
    """Translates spacial instructions.
    
    $$center$$: requires axis index and returns a centered pos value for the given axis
    $$n/n$$: requires axis index and outputs the given fraction of the given axis
    $$extreme(class_object)$$: requires axis index and outputs the right/top border of the object
    
    <<object_nickname>>: refers to the object_class of the dynamic object with given nickname. You can also use <<self>> to refer to the current object
    $window$: automatically replaced with current_window"""
    #d_print(this_function)
    output_value=this_function
    last_function=""
    while output_value!=last_function:
        #d_print(output_value)
        last_function=output_value
        output_value=output_value.replace("§§","")
        output_value=output_value.replace("<<self>>","self.object_class")
        output_value=sub("<<(.*)>>","self.get_object_class(current_canvas,current_window,nickname=\"\g<1>\",space_update=True).object_class",output_value)
        output_value=sub("\$\$extreme\((.*)\)\$\$","(\g<1>.size[%i]+\g<1>.pos[%i])"%(axis,axis),output_value)
        output_value=output_value.replace("$$center$$","(current_window.size[%i]/2)-(self.object_class.size[%i]/2)"%(axis,axis)) if "$$center$$"in output_value else output_value
        output_value=sub("\$\$(\-?\d*)/(\d*)\$\$","(int(\g<1>)*current_window.size[%i])/int(\g<2>)"%(axis),output_value)
        output_value=output_value.replace("$window$","current_window")
    if ("$$" in last_function or "<<" in last_function) or ("$$" in last_function and "<<" in last_function):
        w_print("Unparsable function string: '%s'"%(last_function))
    #d_print(output_value)
    return output_value
def function_add(base_function,value):
    """Sums given value to all the values between "§§" in the base_function
    
    Example: function_add("§§10§§/100",10) outputs "§§20§§/100" """
    output_value=base_function
    for base_search in findall("§§(\-?\d*)§§",str(output_value)):
        output_value=sub("§§(\-?\d*)§§","§§%i§§"%(int(base_search)+value),output_value)
    return output_value
