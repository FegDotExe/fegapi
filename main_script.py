import logging
import os, sys
from re import search, sub
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
    #FIXME: what if instead of vertical offset, I use vertical_size and translate it through translate_function?
    def __init__(self,this_object,current_canvas,nickname=None,proportions=None,custom_size=None,custom_pos=None):
        """:param this_object: a kivy.graphics object
        :param current_canvas: the widget in which the object is
        :param str nickname: a name to recognize this object; if not set, is equal to the object's uid
        :param tuple custom_size: a tuple of two functions which define the object's size when the update_space() method is called. Both can be set as None.
        :param tuple custom_pos: a tuple of two functions which define the object's pos when the update_space() method is called. Both can be set as None.
        :param proportions: proportions by which the object is downscaled in the format "n:n"
        """
        self.uid=this_object.uid
        self.object_class=this_object
        self.nickname=nickname if nickname!=None else this_object.uid
        self.proportions=proportions if proportions!=None else None
        self.custom_pos=custom_pos if custom_pos!=None else None
        self.custom_size=custom_size if custom_size!=None else None
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

        self.object_class.pos=(pos_x,pos_y)

    def get_object_ind_by_name(self,name,current_canvas):
        """Get an object's index in a canvas' objects_list searching by its name. If no match is found, the returned value is -1"""
        output_value=-1
        i=0
        for oggetto in current_canvas.objects_list:
            if oggetto.nickname==name:
                output_value=i
            i+=1
        return output_value
    def get_object_class(self,current_canvas,nickname=None,space_update=False):
        """Returns an object class, found by using the given parameters"""
        output_value=None
        if nickname!=None:
            output_value=current_canvas.objects_list[self.get_object_ind_by_name(nickname,current_canvas)]
        if space_update:
            output_value.update_space(current_canvas)
        return output_value

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
    
    <<object_nickname>>: refers to the object_class of the dynamic object with given nickname. You can also use <<self>> to refer to the current object"""
    output_value=this_function
    last_function=""
    while output_value!=last_function:
        last_function=output_value
        output_value=output_value.replace("<<self>>","self.object_class")
        output_value=sub("<<(.*)>>","self.get_object_class(current_canvas,nickname=\"\g<1>\",space_update=True).object_class",output_value)
        output_value=sub("\$\$extreme\((.*)\)\$\$","(\g<1>.size[%i]+\g<1>.pos[%i])"%(axis,axis),output_value)
        output_value=output_value.replace("$$center$$","(current_window.size[%i]/2)-(self.object_class.size[%i]/2)"%(axis,axis)) if "$$center$$"in output_value else output_value
        output_value=sub("\$\$(\d*)/(\d*)\$\$","(int(\g<1>)*current_window.size[%i])/int(\g<2>)"%(axis),output_value)
    if ("$$" in last_function or "<<" in last_function) or ("$$" in last_function and "<<" in last_function):
        w_print("Unparsable function string: '%s'"%(last_function))
    #d_print(output_value)
    return output_value
