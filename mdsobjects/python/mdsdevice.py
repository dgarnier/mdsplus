from treenode import TreeNode
from compound import *
from _treeshr import TreeStartConglomerate

class Device(TreeNode):
    """Used for device support classes. Provides ORIGINAL_PART_NAME method and allows referencing of subnodes as conglomerate node attributes.

    Use this class as a superclass for device support classes. When creating a device support class include a class attribute called part_names
    as a tuple of strings of the node names of the devices members (not including the head node). You can also include a part_dict
    class attribute consisting of a dict() instance whose keys are attribute names and whose values are nid offsets. If you do
    not provide a part_dict attribute then one will be created from the part_names attribute where the part names are converted
    to lowercase and the colons and periods are replaced with underscores. Referencing a part name will return another instance of the same
    device with that node as the node in the Device subclass instance. The Device class also supports the part_name and original_part_name
    attributes which is the same as doing devinstance.PART_NAME(None).

    Sample usage1::
    
       from MDSplus import Device

       class mydev(Device):
           part_names=(':COMMENT',':INIT_ACTION',':STORE_ACTION','.SETTINGS','.SETTINGS:KNOB1','.SIGNALS','.SIGNALS:CHANNEL_1')

           def init(self,arg):
               knob1=self.settings_knob1.record
               return 1

           def store(self,arg):
               from MDSplus import Signal
               self.signals_channel_1=Signal(32,None,42)

    Sample usage2::

       from MDSplus import Device

       class mydev(Device):
           part_names=(':COMMENT',':INIT_ACTION',':STORE_ACTION','.SETTINGS','.SETTINGS:KNOB1','.SIGNALS','.SIGNALS:CHANNEL_1')
           part_dict={'knob1':5,'chan1':7}

           def init(self,arg):
               knob1=self.knob1.record
               return 1

           def store(self,arg):
               from MDSplus import Signal
               self.chan1=Signal(32,None,42)
               
    If you need to reference attributes using computed names you can do something like::

        for i in range(16):
            self.__setattr__('signals_channel_%02d' % (i+1,),Signal(...))
    """
    
    def __new__(cls,node):
        """Create class instance. Initialize part_dict class attribute if necessary.
        @param node: Not used
        @type node: TreeNode
        @return: Instance of the device subclass
        @rtype: Device subclass instance
        """
        if cls.__name__ == 'Device':
            raise TypeError,"Cannot create instances of Device class"
        if not hasattr(cls,'initialized'):
            if hasattr(cls,'parts'):
                cls.part_names=list()
                for elt in cls.parts:
                    cls.part_names.append(elt['path'])
            if hasattr(cls,'part_names') and not hasattr(cls,'part_dict'):
                cls.part_dict=dict()
                for i in range(len(cls.part_names)):
                    try:
                        cls.part_dict[cls.part_names[i][1:].lower().replace(':','_').replace('.','_')]=i+1
                    except:
                        pass
            cls.initialized=True
        return super(Device,cls).__new__(cls,node)

    def __init__(self,node):
        """Initialize a Device instance
        @param node: Conglomerate node of this device
        @type node: TreeNode
        @rtype: None
        """
        try:
            self.nids=node.conglomerate_nids.nid_number
            self.head=int(self.nids[0])
        except Exception,e:
            self.head=node.nid
        super(Device,self).__init__(node.nid,node.tree)

    def ORIGINAL_PART_NAME(self,arg):
        """Method to return the original part name.
        Will return blank string if part_name class attribute not defined or node used to create instance is the head node or past the end of part_names tuple.
        @param arg: Not used. Placeholder for do method argument
        @type arg: Use None
        @return: Part name of this node
        @rtype: str
        """
        name = ""
        if self.nid != self.head:
            try:
                name = self.part_names[self.nid-self.head-1].upper()
            except:
                pass
        return name
    PART_NAME=ORIGINAL_PART_NAME

    def __getattr__(self,name):
        """Return TreeNode of subpart if name matches mangled node name.
        @param name: part name. Node path with colons and periods replaced by underscores.
        @type name: str
        @return: Device instance of device part
        @rtype: Device
        """
        if name == 'part_name' or name == 'original_part_name':
            return self.ORIGINAL_PART_NAME(None)
        try:
            return self.__class__(TreeNode(self.part_dict[name]+self.head,self.tree))
        except KeyError:
            return super(Device,self).__getattr__(name)

    def __setattr__(self,name,value):
        """Set value into device subnode if name matches a mangled subpart node name. Otherwise assign value to class instance attribute.
        @param name: Name of attribute or device subpart
        @type name: str
        @param value: Value of the attribute or device subpart
        @type value: varied
        @rtype: None
        """
        try:
            TreeNode(self.part_dict[name]+self.head,self.tree).record=value
        except KeyError:
            super(Device,self).__setattr__(name,value)

    def Add(cls,tree,path):
        TreeStartConglomerate(tree,len(cls.parts)+1)
        head=tree.addNode(path,'DEVICE')
        head.record=Conglom('__python__',cls.__name__,None,"from %s import %s" % (cls.__module__[0:cls.__module__.index('.')],cls.__name__))
        head.write_once=True
        for elt in cls.parts:
            node=tree.addNode(path+elt['path'],elt['type'])
            if 'value' in elt:
                node.record=elt['value']
            if 'valueExpr' in elt:
                node.record=eval(elt['valueExpr'])
            if 'options' in elt:
                for option in elt['options']:
                    exec 'node.'+option+'=True'
    Add=classmethod(Add)


