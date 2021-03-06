"""
Math Inspector: a visual programing environment for scientific computing with python
Copyright (C) 2018 Matt Calhoun

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import tkinter as tk
from util import argcount, unique_name
from settings import Color, Widget, ButtonRight
from widget.canvas import PanZoomDragCanvas, Item
from widget import ContextMenu, Popup, InfoBox

class WorkSpace(PanZoomDragCanvas):
	def __init__(self, app, *args, **kwargs):
		PanZoomDragCanvas.__init__(self, app, highlightthickness=4, highlightbackground=Color.BLACK, *args, **kwargs)
		self.connect = { "input": None, "output": None, "input_id": None }
		self.hover_input = None
		self.hover_editable_item = None
		self.editable_item = None
		self.log = InfoBox(self)
		self.contextmenu = ContextMenu(app)
		self.contextmenu.set_menu(items=[{ "label": "Delete", "command": self._on_delete }])		
		self.tag_bind("draggable", ButtonRight, self._on_contextmenu)
		self.tag_bind("input", "<Enter>", self._on_enter_input)
		self.tag_bind("input", "<Leave>", self._on_leave_input)
		self.tag_bind("input", "<Button-1>", lambda event: self._on_start_output(event, is_input=True))
		self.tag_bind("input", "<ButtonRelease-1>", lambda event: self._on_connect_output(event, is_input=True))
		self.tag_bind("input", "<B1-Motion>", self._on_move_output)
		self.tag_bind("output", "<Enter>", self._on_enter_output)
		self.tag_bind("output", "<Leave>", self._on_leave_output)
		self.tag_bind("output", "<Button-1>", self._on_start_output)
		self.tag_bind("output", "<ButtonRelease-1>", self._on_connect_output)
		self.tag_bind("output", "<B1-Motion>", self._on_move_output)        
		self.tag_bind("output_wire", "<Enter>", self._on_enter_wire)
		self.tag_bind("output_wire", "<Leave>", self._on_leave_wire)
		self.tag_bind("output_wire", "<Button-1>", self._on_start_output)
		self.tag_bind("output_wire", "<ButtonRelease-1>", self._on_connect_output)
		self.tag_bind("output_wire", "<B1-Motion>", self._on_move_output)
		self.tag_bind("editable", "<Motion>", self._on_motion_editable)
		self.tag_bind("editable", "<Leave>", self._on_leave_editable)
		self.tag_bind("editable", "<Button-1>", self._on_click_editable)

	def get_state(self):
		result = { "zoomlevel": self.zoomlevel, "items": [] }
		for x in self.items: 
			if isinstance(self.items[x], Item):
				item = self.items[x]
				args = {}
				kwargs = {}
				for j in item.args:
					args[j] = {
						"value": None if "value" not in item.args[j] else item.args[j]["value"],
						"connection": None if not item.args[j]["connection"] else item.args[j]["connection"].name
					}

				for j in item.kwargs:
					kwargs[j] = {
						"value": None if "value" not in item.kwargs[j] else item.kwargs[j]["value"],
						"connection": None if not item.kwargs[j]["connection"] else item.kwargs[j]["connection"].name
					}

				result["items"].append({
					"name": item.name,
					"line_color": item.line_color,
					"sticky_graph": item.sticky_graph,
					"position": item.get_position(),
					"args": args,
					"kwargs": kwargs
				})
		return result

	def set_state(self, state):
		self.zoomlevel = state["zoomlevel"]
		for i in state["items"]: 
			x,y = i["position"]
			item = self.get_item(i["name"])
			item.move(x,y)

			# system for working with older save files to not crash everything
			if "line_color" in i:
				item.set_color(i["line_color"])
			if "sticky_graph" in i and i["sticky_graph"]:
				item.toggle_sticky()

			for j in i["args"]:
				item.setarg(j, i["args"][j]["value"])
				output_item = self.get_item(i["args"][j]["connection"])
				if output_item:
					output_item.set_output_connection(item, item.args[j]["input"])
					output_item.move()

			for j in i["kwargs"]:
				item.setarg(j, i["kwargs"][j]["value"])
				output_item = self.get_item(i["kwargs"][j]["connection"])
				if output_item:
					output_item.set_output_connection(item, item.kwargs[j]["input"])
					output_item.move()

		# for i in state["items"]: 
		# 	item = self.get_item(i["name"])	
		# 	if i["output_connection"]:
		# 		item.set_output_connection( self.get_item(i["output_connection"]) )

	def _on_motion_editable(self, event):
		item = self.get_closest(event.x, event.y)
		if self.event != "drag" and item == self.selected:
			self.hover_editable_item = item
			closest = self.find_closest(event.x, event.y)[0]
			if "editable" in self.gettags(closest):
				self.editable_item = closest
				self.hover_editable_item.config(hover_editable=("enter", self.editable_item))

	def _on_leave_editable(self, event):
		if self.hover_editable_item:
			self.hover_editable_item.config(hover_editable=("leave", self.editable_item))
		self.hover_editable_item = None
		self.editable_item = None

	def _on_click_editable(self, event):
		# @TODO: when object is in edit mode, enable b1-motion event
		item = self.get_closest(event.x, event.y)
		if self.hover_editable_item == self.selected:
			self.event = "edit"
			self.hover_editable_item = item
			item.canvasentry.edit(self.editable_item)

		if not self.hover_editable_item:
			closest = self.find_closest(event.x, event.y)[0]
			if "editable" in self.gettags(closest):
				self.editable_item = closest
				self.hover_editable_item = item
				self.hover_editable_item.config(hover_editable=("enter", self.editable_item))

	def _on_contextmenu(self, event):
		item = self.get_closest(event.x, event.y)
		if self.multiselect["items"]:
			self.contextmenu.set_menu([{ 
				"label": "Delete selected items...", 
				"command": self._on_delete 
			}])
		else:
			transform = []
			methods = []
			graph = []
			extras = []
			for fn in item.methods():
				attr = getattr(item.value, fn)	
				if argcount(attr) == 0:
					transform.append({
						"label": fn,
						"command": lambda attr=attr: self._on_item_method(item, attr)	
					})
				else:
					methods.append({
						"label": fn,
						"command": lambda fn=fn: Popup(self.app, item.name + "." + fn, self.app, obj=getattr(item.value, fn), canvas_item=item)
					})

			if isinstance(item.value, (int, float)):
				extras.append({
					"label": "Animate",
					"command": lambda: self.animate(item)	
				})

			if len(item.kwargs) > 0:
				extras.append({
					"label": "Hide kwargs" if item.show_kwargs else "Show kwargs",
					"command": item.toggle_kwargs
				})

			# if item.isgraphable ... ?
			graph.append({
				"label": "Sticky       ✓" if item.sticky_graph else "Sticky",
				"command": item.toggle_sticky
			})	

			graph.append({
				"label": "Set color     " + item.line_color if item.line_color != Color.BLUE else "Set color",
				"command": lambda item=item: Popup(self.app, item.name + ".set_color", self.app, obj=item.set_color, canvas_item=item)
			})	

			self.contextmenu.set_menu(transform + [{
				"separator": None
			}, { 
				"label": "methods", 
				"menu": methods
			}, { 
				"label": "graph", 
				"menu": graph
			}, {
				"separator": None
			}] + extras + [{ 
				"label": "Rename...", 
				"command": lambda: None
			}, { 
				"label": "Delete", 
				"command": self._on_delete 
			}])
			self.app.select(item.name)
		self.contextmenu.show(event, item.name)

	def _on_item_method(self, item, attr):
		result = attr()
		item.set_value(item.value)
		if isinstance(result, bool):
			self.log.show(str(result))
		elif result:
			name = unique_name(self.app, item.name + "_" + attr.__name__)
			self.app.objects[name] = result

	def animate(self, item):
		Popup(self.app, "Animate", self.app, 
			obj=self.timer(item.value), 
			canvas_item=None, 
			callback=lambda *args, **kwargs: self.app.timer(item.name, *args, **kwargs)
		)

	def timer(self, s):		
		return lambda a, start=s, stop=10, step=1, delay=100, colorchange=False, color=0x000000: None

	def select(self, name):
		if name is None and self.selected is not None:
			self.itemconfig(self.selected.canvas_id, fill=Color.BLACK)
			self.itemconfig(self.selected.variable_label, fill=Color.WHITE)
			self.selected = None
			self.app.select(None)
			return
		
		if self.selected is not None: 
			self.itemconfig(self.selected.canvas_id, fill=Color.BLACK)
			self.itemconfig(self.selected.variable_label, fill=Color.WHITE)

		if isinstance(name, Item):
			self.selected = name
		else: 
			for canvas_item in self.items:
				if name == self.items[canvas_item].name:
					self.selected = self.items[canvas_item]

		if self.selected:
			self.itemconfig(self.selected.canvas_id, fill=Color.VERY_LIGHT_PURPLE)
			self.itemconfig(self.selected.variable_label, fill=Color.WHITE)

	def get_item(self, key, idx=False):
		for j in self.items:
			if self.items[j].name == key:
				return (self.items[j], j) if idx else self.items[j]

		return (None, None) if idx else None

	def set_items(self, items):
		# @TODO: make a system for loading and saving state with positions and connections, I guess into an object to be pickeled I like that system
		self.items = items
		for j in self.items:
			self.update_object(self.items[j])

	def update_object(self, key):
		item, idx = self.get_item(key, idx=True)
		if item:
			item.set_value(self.app.objects[key])			
		else:
			obj = self.app.objects[key]
			item = self.create_item(obj, key)

	def delete_object(self, key):
		item, idx = self.get_item(key, idx=True)
		del_list = []
		del_input_id = None
		del_output_id = None
		del_output_wire_id = None
		for j in self.canvas_ids:				
			if j in item.children:
				del_list.append(j)

		for j in item.args:
			del self.input_nodes[self.input_nodes.index(item.args[j]["input"])]						
		
		del self.output_nodes[self.output_nodes.index(item.output)]						
		del self.output_nodes[self.output_nodes.index(item.output_wire)]						
		for k in del_list:
			del self.canvas_ids[k]
		
		item.destroy()
		del self.items[idx]

	def _on_delete(self):
		if self.multiselect["items"]:
			for canvas_id in self.multiselect["items"]:
				del self.app.objects[self.items[canvas_id].name]
		else:
			del self.app.objects[self.contextmenu.key]

	def _on_enter_input(self, event):
		if self.event == "connect": return

		closest = None
		overlapping = self.find_overlapping(
			event.x - Widget.HITBOX, event.y - Widget.HITBOX, 
			event.x + Widget.HITBOX, event.y + Widget.HITBOX
		)
		for j in overlapping:
			if "input" in self.gettags(j):
				closest = j
				break
		if not closest: return
		self.hover_input = self.get_parent(closest).getarg("input", closest)
		if self.hover_input and self.hover_input["connection"]:
			self.hover_input["connection"].config(hover=Color.WIRE_INACTIVE)
			
	def _on_leave_input(self, event):
		if self.event == "connect" or not self.hover_input: return

		if self.hover_input and self.hover_input["connection"]:
			self.hover_input["connection"].config(hover=Color.ACTIVE_WIRE)

		self.hover_input = None

	def _on_enter_output(self, event):
		item = self.get_closest(event.x, event.y, self.output_nodes)
		if item:
			item.config(hover=Color.WIRE_INACTIVE)

	def _on_leave_output(self, event):
		if self.event == "connect": return		
		item = self.get_closest(event.x, event.y, self.output_nodes)
		if not item: return

		if item.output_connection:
			item.config(hover=Color.ACTIVE_WIRE)
		else:
			item.config(hover=Color.EMPTY_NODE)

	def _on_start_output(self, event, is_input=False):
		if is_input:
			input_id = self.get_closest(event.x, event.y, self.input_nodes, parent=False)
			item = self.get_parent(input_id)
			for j in item.args:
				if input_id == item.args[j]["input"]:
					self.connect["output"] = item.args[j]["connection"]
			for j in item.kwargs:
				if input_id == item.kwargs[j]["input"]:
					self.connect["output"] = item.kwargs[j]["connection"]
		else:
			self.connect["output"] = self.get_closest(event.x, event.y, self.output_nodes)
		
		if self.connect["output"]:
			self.app.select(self.connect["output"].name)

	# @REFACTOR: move all logic for color/ui changes to canvasitem
	# @REFACTOR: get rid of self.input_nodes and use canvas tags
	def _on_move_output(self, event):
		self.event = "connect"

		if self.connect["output"]:
			self.connect["output"].config(hover=Color.WIRE_INACTIVE)
			self.connect["output"].config(border="hide")
			if self.connect["output"].output_connection:
				self.connect["output"].output_connection.config(border="hide")
			if self.connect["input_id"]:
				self.itemconfig(self.connect["input_id"], fill=Color.EMPTY_NODE)
			self.connect["output"].set_output_connection(None)
		
		input_item = self.get_closest(event.x, event.y, self.input_nodes, parent=False)

		if input_item:
			self.connect["input_id"] = input_item
			other = self.get_parent(input_item)
			x1,y1,x2,y2 = self.coords(input_item)
			self.connect["output"].move_wire(x1 + (x2 - x1)/2, y1 + (y2 - y1)/2)
			self.connect["output"].config(output=Color.ACTIVE_WIRE)
			self.itemconfig(input_item, fill=Color.ACTIVE_WIRE)
			self.connect["output"].config(border="show")
			other.config(border="show")
		elif self.connect["output"]:
			self.connect["output"].move_wire(event.x, event.y)
			if self.connect["input"]:
				self.connect["output"].config(border="hide")
				self.connect["input"].config(border="hide")
				self.connect["input"] = None

		if input_item:
			self.connect["input"] = other

	def _on_connect_output(self, event, is_input=False):
		if self.event is not "connect": return

		if self.connect["output"]:
			if self.connect["input"]:
				self.connect["output"].set_output_connection(self.connect["input"], self.connect["input_id"])

				if self.app.on_set_object(self.connect["output"].name):
					self.app.select(self.connect["input"].name)
				else:
					self.connect["output"].config(hover=Color.EMPTY_NODE)
			else:
				self.connect["output"].config(hide_wire=True)

		if self.connect["input"]:
			try:
				val = self.connect["input"].get_output(raise_err=True)
			except Exception as err:
				self.log.show(err)
				self.connect["output"].set_output_connection(None);
				self.connect["output"].config(hide_wire=True)
				self.itemconfig(self.connect["input_id"], fill=Color.EMPTY_NODE)

		self.connect["output"] = None
		self.connect["input"] = None
		self.event = None
				
	def _on_enter_wire(self, event):
		item = self.get_parent( self.find_closest(event.x, event.y)[0] )

		if item.output_connection:
			item.config(hover=Color.WIRE_INACTIVE)

	def _on_leave_wire(self, event):
		item = self.get_parent( self.find_closest(event.x, event.y)[0] )

		if item and item.output_connection:
			item.config(hover=Color.ACTIVE_WIRE)

	def _on_click_wire(self, event):
		closest = self.find_closest(event.x, event.y)[0]
		if not closest: return

		self.event = "connect"
		self.connect["output"] = self.get_parent(closest)				
