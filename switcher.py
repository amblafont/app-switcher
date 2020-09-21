# https://github.com/emerinohdz/status-title-bar
# https://extensions.gnome.org/extension/59/status-title-bar/

# 'print' is like in python3
from __future__ import print_function

from ewmh import EWMH



from contextlib import contextmanager
import Xlib.display
from Xlib import protocol, Xatom
from getkey import getkey, keys

from anytree import Node, RenderTree, Resolver
import sys
import os

ewmh = EWMH()


# The custom xproperty set to remember the path of a winsow
path_xproperty_name =  "CUSTOM_TREE_PATH"

# the first argument is a window PID
if (len(sys.argv) > 1):
   selected_wid = int(sys.argv[1])
   print("Selected window id: ", selected_wid)
   print()
else:
   selected_wid = None


display = Xlib.display.Display()
root = display.screen().root

# this is taken from https://gist.github.com/ssokolow/e7c9aae63fb7973e4d64cff969a78ae8

# Prepare the property names we use so they can be fed into X11 APIs
NET_ACTIVE_WINDOW = display.intern_atom('_NET_ACTIVE_WINDOW')
NET_WM_NAME = display.intern_atom('_NET_WM_NAME')  # UTF-8
WM_NAME = display.intern_atom('WM_NAME')           # Legacy encoding

# this is taken from https://gist.github.com/ssokolow/e7c9aae63fb7973e4d64cff969a78ae8
# get the window object associated with an id
# use:
# with window_obj(wid) as wo:
@contextmanager
def window_obj(wid):
    """Simplify dealing with BadWindow (make it either valid or None)"""
    window_obj = None
    if wid:
        try:
            window_obj = display.create_resource_object('window', wid)
        except Xlib.error.XError:
            pass
    yield window_obj


def win_get_name(win_obj):
    return ewmh.getWmName(win_obj)

# These functions were inspired by xproperty python git repo

def atom_i2s(integer):
  return display.get_atom_name(integer)

def atom_s2i(string):
  i = display.get_atom(string, only_if_exists=False)
  if i == Xlib.X.NONE:
    raise ValueError('No Atom interned with that name.')
  else:
    return i

# focus on (switch to) a specific window
# Unfortunately, I haven't found how to do it programmatically
def win_focus(win):
    cmd = "wmctrl -i -a " + str(win.id)
    print(cmd)
    os.system(cmd)
#    ewmh.setActiveWindow(win)
#    ewmh.setCurrentDesktop(ewmh.getWmDesktop(win))
#    ewmh.display.flush()

# Unfortunately, I haven't found how to set a custom property using in python xlib
def win_setProperty(win, xprop_name, data):
    cmd = 'xprop -id %d -f %s 8s -set %s "%s"' % (win.id, xprop_name, xprop_name, data)
    print (cmd)
    os.system(cmd)
    # property = atom_s2i(xprop_name)
    # window.change_property(property, Xatom.STRING, 8, str(data)) #, onerror = (lambda x , y : print("Erreur")))
    # window.query_tree()

    # display.screen().root.query_tree()
 

def wid_set_path(wid, value):
    with window_obj(wid) as win:
        win_setProperty(win, path_xproperty_name, "/".join(value))



# get the path associated to a window 
# or None if the property does not exist
# adapted from get_property, from the xproperty github repo
def win_get_path(window):
   property = window.get_property(atom_s2i(path_xproperty_name), 0, 0, pow(2,32)-1)
   if property is None:
       return None
   assert property._data['bytes_after'] == 0
   property_type = atom_i2s(property._data['property_type'])
   if property_type == 'STRING':
     # strings should be served byte-wise
     assert property.format == 8;
     # string arrays are separated by \x00; some have one at the end as well
     values = property.value.split('/')
     return values
   else:
     return None
     # raise NotImplementedError('Im sorry, I can handle only STRINGs so far.')


 
# find a node among the descendant, following
# the path (array of strings, as the successive names)
# Creates new nodes if needed.
def node_find_by_path_create(node, path):
    searching_node = node
    for el in path:
        found = False
        for child in searching_node.children:
            if child.name == el:
                searching_node = child
                found = True
                break
        if not found:
            searching_node = Node(el, parent = searching_node)
    return searching_node



# if a node is at the position /ROOT/a/b,
# then returns the string /a/b
def node_str_path(tree):
    node = tree
    path = ""
    while node.parent != None:
        path = '/' + node.name + path
        node = node.parent
    if path == "":
        return "/"
    return path

def node_may_get_parent(n):
    if n.parent != None:
        return n.parent
    else:
        return n

def node_dump(mainnode):
  for pre, fill, node in RenderTree(mainnode):
      print("%s%s" % (pre, node.name))


# return a list of nodes matching
# the path provided by cible
# which may be a string like '../cu*/wer'
def node_search(tree, cible):
    s = cible
    if s == "":
        return []
    if s[0] == '/':
        s = '/' + tree.root.name + s
    r = Resolver('name')
    return r.glob(tree, s + '*')

def node_has_wins(t):
    return hasattr(t, 'w')

def node_get_wins(t):
    if node_has_wins(t):
        return t.w
    else:
        return []

def node_add_win(t, win):
    if node_has_wins(t):
        t.w.append(win)
    else:
        t.w = [win]

# print the node path, with the number of children
# in green if it has windows associated.
def node_print_path(node):
    if node_has_wins(node):
        # green
        # color = "\033[0;32;40m"
        color = "\033[32m"
    else:
        # red
        color = ""
        # color = "\033[0;31;40m" 
    blackcolor = "\033[m"
    s = "%s%s%s (%d)" % (color, node_str_path(node), blackcolor, len(node.children))

    print (s)

# the tree of windows, following the path hierarchy
tree_wins = Node("ROOT")

# get the list of windows managed by the window manager
for window in ewmh.getClientList():
     data = win_get_path(window)
     if data != None:
        n = node_find_by_path_create(tree_wins, data)
        if node_has_wins(n):
            print("Multiple windows with same path: ", node_str_path(n))
        node_add_win(n, window)


if selected_wid == None:
    selected_path = []
    selected_title = "(no selected window)"
else:
  with window_obj(selected_wid) as selected_win:
      selected_path = win_get_path(selected_win)
      selected_title = win_get_name(selected_win)
      if selected_path == None:
          selected_path = []

print('/' + "/".join(selected_path) , "> ", selected_title) 
print()
curNode = node_may_get_parent(node_find_by_path_create(tree_wins, selected_path))

print()
print("ESC: Quit")
print("F2: Set the path of the selected window")
print("Otherwise, type the path of some other window to jump to")
print()
key = getkey()
matching_node = None
if key == keys.F2:
    if selected_wid == None:
        print("Impossible to set the path: No selected window")
        exit()
    names = raw_input("Set the path, from the root (e.g. tes/tes) : /")
    with window_obj(selected_wid) as cur_win:
        arr_names = names.split('/')
        wid_set_path(selected_wid, arr_names)
    exit()

if key == keys.ESC:
    exit()

# current path entered by the user
cur_path = ""
# nodes matching the current path
matching_nodes = []
cursor = 0

while key != keys.ENTER:
    if key == keys.ESC:
        exit()
    else:
        if key == keys.BACKSPACE:
           cur_path = cur_path[:-1]
        # auto-completion
        elif key == keys.TAB:
           if matching_nodes != []:
               cur_path = node_str_path(matching_nodes[0])
               # if the matching node has no attached window
               # we know we won't stop at this node,
               # so we can add a '/'
               if not node_has_wins(matching_nodes[0]):
                   cur_path += "/"
        elif key == keys.DOWN:
            if cursor + 1 < len(matching_nodes):
                cursor += 1
        elif key == keys.UP:
            if cursor > 0:
                cursor -= 1
        else:
           cur_path += key

        if key != keys.DOWN and key != keys.UP:
            cursor = 0

        # print the whole hierarchy if we are at the top
        if cur_path == "/":
             node_dump(tree_wins)
        else:
              # get the nodes that match the path
              matching_nodes = node_search(curNode, cur_path)
              print()
              print()
              for i in range(0,len(matching_nodes)):
                  if i == cursor:
                     print ("> ", end='')
                  else:
                     print ("  ", end='')
                  node_print_path(matching_nodes[i])
        print()
        print(cur_path, end = '')
        sys.stdout.flush()

    key = getkey()

print()


if cursor >= len(matching_nodes):
    print("No matching path.")
    exit()

matching_node = matching_nodes[cursor] 

if node_has_wins(matching_node):
    w = node_get_wins(matching_node)[0]
    print("found window:", win_get_name(w))
    win_focus(w)
else:
    print("No window there")
    node_dump (node)

    


