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

from tkinter import ttk
from settings import Color

def apply(app):
	app.set_theme("arc")		
	theme = ttk.Style(app)		
	for widget in configure:
		theme.configure(widget, **configure[widget])

configure = {
	"Treeview": {
		"background": Color.ALT_BACKGROUND, 
		"fieldbackground": Color.ALT_BACKGROUND, 
		"foreground": Color.VERY_LIGHT_GREY	
	},

	"TPanedwindow": {
		"background": Color.BLACK
	}
}

treenotebook = {
	"expandtabs": True, 
	"tabbackground": Color.BLACK, 
	"background": Color.BLACK, 
	"highlightthickness": 4, 
	"highlightbackground": Color.BLACK
}

treenotebook_tab = {
	"font": "SourceSansPro 12 bold", 
	"background": Color.BLACK, 
	"foreground": Color.WHITE,
	"selected_bg": Color.BLACK,
	"selected_fg": Color.ORANGE,
	"hover": Color.VERY_DARK_GREY
}

# _map = {
	
# }