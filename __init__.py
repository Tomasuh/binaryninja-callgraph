from binaryninja import *
import graphviz as gv, os

styles = {
     'graph': {
         'label': 'Filename',
         'fontsize': '16',
         'fontcolor': 'black',
         'bgcolor': 'white',
         'rankdir': 'TB',
         'splines': 'ortho',
         'ordering': 'out',
     },
     'nodes': {
         'fontname': 'Helvetica',
         'shape': 'box',
         'fontcolor': 'white',
         'color': 'white',
         'style': 'filled',
         'fillcolor': '#006699',
                'splines': 'spline',
     },
     'edges': {
         'style': 'filled',
         'color': 'black',
         'arrowhead': 'open',
         'fontname': 'Courier',
         'fontsize': '12',
         'fontcolor': 'white',
                'splines': 'polyline',
     }
}

def apply_styles(graph, styles):
     graph.graph_attr.update(
         ('graph' in styles and styles['graph']) or {}
     )
     graph.node_attr.update(
         ('nodes' in styles and styles['nodes']) or {}
     )
     graph.edge_attr.update(
         ('edges' in styles and styles['edges']) or {}
     )
     return graph

def add_child(g,name,labelName):
    g.node(name,labelName)
        
def add_call(g,nodeFrom, nodeTo):
    g.edge(str(nodeFrom),str(nodeTo))

traversalDepth = 0
adrRngToNotTraverse = [] #(start,end) sections to not be traversed

def sectionsToNotTraverse(bv,sections):
	global adrRngToNotTraverse
	adrRngToNotTraverse = []
	for section in sections:
		sect = bv.sections.get(section)
		if sect:
			adrRngToNotTraverse.append((sect.start, sect.end))

def shouldNotBeTrav(bv, function):
	for start,end in adrRngToNotTraverse:
		if start <= function.start and end > function.start:
			return True
	return False

def goOn(bv,function):

	g = gv.Digraph(format='png')

	funcsToTraverse = [(0,function)] #(traversalLevel, function)

	edges = []

	funcsToShowInLabel = {} #['funcname']=[show]
	functionCalls = {} # ['funcname']=[calls]

	while funcsToTraverse!=[]:
		traverseLevel, func = funcsToTraverse.pop()

		if traversalDepth > 0 and traverseLevel>=traversalDepth:
			continue

		callsFuncsToTraverseNames = []
		callsFuncsToShowInLabel = []

		for block in func.low_level_il:
			for il in block:
				if il.operation != enums.LowLevelILOperation.LLIL_CALL and \
					il.operation!=enums.LowLevelILOperation.LLIL_JUMP_TO and \
					il.operation!=enums.LowLevelILOperation.LLIL_JUMP:
					continue

				try:
					name = bv.get_functions_at(il.operands[0].value)[0].name
					calls = bv.get_functions_at(il.operands[0].value)[0]
		
					if shouldNotBeTrav(bv,calls):
						continue

					elif (func.name, calls.name) not in edges:
						edges.append((func.name, calls.name))
						callsFuncsToTraverseNames.append(calls.name)		

					
					funcsToTraverse.append((traverseLevel+1,calls))


				except AttributeError:
					pass

		add_child(g,func.name, func.name)

		for funcNames in callsFuncsToTraverseNames:
			add_call(g,func.name, funcNames)
			
	(styles["graph"])["label"] = bv.file.filename.split("/")[-1]
	apply_styles(g, styles)

	filename = g.render(filename='/tmp/graph.dot', view=True)
	log.log.log_alert("Dot file saved to: /tmp/graph.dot")


def go(bv,function):
	global traversalDepth

	sectionsDefault = [".plt"]
	s = get_text_line_input("Enter sections to not be traversed, separated by comma.\nDefault one is '.plt'", "Sections to not traverse")
	if s:
		sections=s.split(",")
	else:
		sections=sectionsDefault

	sectionsToNotTraverse(bv,sections)

	d = get_text_line_input("Enter traversal depth, 0 for unlimited (default).", "Traversal depth")
	if not d:
		d="0"
	traversalDepth = int(d)

	goOn(bv,function)

PluginCommand.register_for_function("Generate function call graph", "Generate function call graph", go)


