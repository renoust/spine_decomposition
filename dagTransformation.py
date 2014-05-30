from tulip import *
import math

class DAGTrans:
	def __init__(self, graph):
		self.sg = graph
		self.degree = self.sg.getDoubleProperty("degree")
		dset = tlp.getDefaultPluginParameters("Degree")
		self.sg.computeDoubleProperty("Degree", self.degree, dset)
		self.viewLabel = self.sg.getLocalStringProperty("viewLabel")
		self.dToN = {}
		self.dList = []
		self.aWeight = self.sg.getDoubleProperty("accumulatedWeight")
		self.aRank = self.sg.getDoubleProperty("abelloRank")
		self.acwP = self.sg.getDoubleProperty("accumulatedWeight/Size")
		self.sizeP = self.sg.getDoubleProperty("size")
		self.outDegP = self.sg.getDoubleProperty("outDegree")
		self.roundP = self.sg.getDoubleProperty("round")
		self.turnP = self.sg.getDoubleProperty("turn")
		self.treated = self.sg.getBooleanProperty("treated")
		self.treated.setAllEdgeValue(False)
		self.lastAbelloRank = 0
	
			
	def computeDirectedGraph(self, metaNodes=False): 
		
		for n in self.sg.getNodes():
			dg = self.degree[n]
			if dg not in self.dToN:
				self.dToN[dg] = []
			self.dToN[dg].append(n)
			self.viewLabel[n] = str(dg).encode("utf-8")
			self.sizeP[n] = 1.0
			
		self.dList = self.dToN.keys()
		self.dList.sort()
		#print self.dList
		
		equivalentSets	= []
			
		viewColor = self.sg.getColorProperty("viewColor")
		for iDList in range(len(self.dList)):
			d = self.dList[iDList]
			nList = self.dToN[d]
			for n in nList:
				self.viewLabel[n] = str(d) #str(iDList) + '/' + str(d)
				for e in self.sg.getInOutEdges(n):
					n2 = self.sg.opposite(e, n)
					[s, t] = self.sg.ends(e)
					d2 = self.degree[n2]
					if d2 < d and t == n2\
					or d2 > d and s == n2:
						self.sg.reverse(e)
					if d2 == d:
						if s == n2:
							if not self.sg.existEdge(n, n2).isValid():
								e2 = self.sg.addEdge(n, n2)
								#viewColor[e2] = tlp.Color(229,206,160)
								viewColor[e2] = tlp.Color(255,0,0,100)
								viewColor[e] = tlp.Color(255,0,0,100)
								
						else:
							if not self.sg.existEdge(n2, n).isValid():
								e2 = self.sg.addEdge(n2, n)
								#viewColor[e2] = tlp.Color(229,206,160)
								viewColor[e2] = tlp.Color(255,0,0,100)
								viewColor[e] = tlp.Color(255,0,0,100)
						inSet = -1
						toDel = []			
						for i in range(len(equivalentSets)):
							sset = equivalentSets[i]
							if n in sset and inSet == -1:
								sset.append(n2)							
								inSet = i
							elif n2 in sset and inSet == -1:
								sset.append(n)
								inSet = i
							elif n in sset and inSet > -1:
								equivalentSets[inSet].extend(sset)
								toDel.append(i)
							elif n2 in sset and inSet > -1:
								equivalentSets[inSet].extend(sset)
								toDel.append(i)
								
						for i in toDel:
							del equivalentSets[i]
					
						if inSet == -1:		
							equivalentSets.append([n,n2])
			
		backup = self.sg.getSuperGraph().addSubGraph()
		backup.setName("1.oriented")
		tlp.copyToGraph(backup, self.sg)
		
		if metaNodes:
			self.lastAbelloRank = 0	
			self.qsg = self.sg.addCloneSubGraph()	
			self.qsg.setName("2.process")		
		
			nodeMap = {}		
			for g in [set(i) for i in equivalentSets]:
				
				mn = self.qsg.createMetaNode(g,False, True)
				self.sizeP[mn] = len(g)
				#print "size of meta node:", len(g)
				
				for n in g:
					nodeMap[n] = mn
				
				#outDeg = self.qsg.outdeg(mn)
				#for e in self.qsg.getOutEdges(mn):
				#	self.aWeight[e] = float(len(g)) / float(outDeg)
					
			for d in self.dToN:
				nList = self.dToN[d]
				for i in range(len(nList)):
					n = nList[i]
					if n in nodeMap:
						nList[i] = nodeMap[n]
				self.dToN[d] = list(set(nList))
			
			backup = self.qsg.getSuperGraph().addSubGraph()
			backup.setName("3.meta")
			#tlp.copyToGraph(backup, self.qsg)
			for n in self.qsg.getNodes():
				backup.addNode(n)
			for e in self.qsg.getEdges():
				backup.addEdge(e)
			self.drawGraph(backup)			
			
			self.metaNodes = metaNodes
			#while(self.decompose()):
			#	print self.lastAbelloRank
			
			#uncomment here for further representations
			#self.redraw()
	
	def decompose(self):
		if not self.metaNodes:
			return False
		
		sources = []
		dToS = {}
		dToSize = {}
		dToAcw = {}
		dToAcwS = {}
		
		for n in self.qsg.getNodes	():
			if not self.treated[n]:
				inDeg = float(self.qsg.indeg(n))
				if inDeg == 0\
				or False not in [self.treated[node] for node in self.qsg.getInNodes(n)]:
					sources.append(n)
					outDeg = float(self.qsg.outdeg(n))
					if outDeg not in dToS:
						dToS[outDeg] = []
					dToS[outDeg].append(n)
					self.outDegP[n] = outDeg
					
					size = self.sizeP[n]
					if size not in dToSize:
						dToSize[size] = []
					dToSize[size].append(n)
					
					acw = size
					for e in self.qsg.getInEdges(n):
						acw += self.aWeight[e]
					self.aWeight[n] = acw
					
					if acw not in dToAcw:
						dToAcw[acw] = []
					dToAcw[acw].append(n)
					
					acw /= float(size)
					self.acwP[n] = acw
					if acw not in dToAcwS:
						dToAcwS[acw] = []
					dToAcwS[acw].append(n)
					
		
		if len(sources) == 0:
			return False
					
		self.lastAbelloRank += 1
		self.lastAbelloRank = 	math.floor(self.lastAbelloRank)

		subrank = 1

		sortingMap = dToAcw

		dToMeta = {}
		degrees = sorted(sortingMap.keys())


		for dg in degrees:
			
			nList = sortingMap[dg]
			#metaList = []
			outDMap = {}
			for n in nList:
				dg = self.qsg.outdeg(n)
				if dg not in outDMap:
					outDMap[dg] = []
				outDMap[dg].append(n)
			
			outDList = sorted(outDMap.keys())
			nList = []
			for d in outDList:
				for n in outDMap[d]:
					nList.append(n)
					
			for sourceNode in nList:
				self.aRank[sourceNode] = self.lastAbelloRank
				self.treated[sourceNode] = True
				
				for e in self.qsg.getInEdges(sourceNode):
					self.viewLabel[e] = "%.3f" % self.aWeight[e]
					
				inWeight = self.aWeight[sourceNode]
						
				outDeg = self.qsg.outdeg(sourceNode)
				for e in self.qsg.getOutEdges(sourceNode):
					acFlow = float(inWeight) / float(outDeg)
					self.aWeight[e] = acFlow
					self.acwP[e] = acFlow
				self.roundP[sourceNode] = self.lastAbelloRank
				self.turnP[sourceNode] = subrank		
				self.viewLabel[sourceNode] = str(int(self.lastAbelloRank))+"."+str(subrank)+"\nw=%.3f"%(inWeight)+"\nw/s=%.3f"%(self.acwP[sourceNode])+"\ns=%.3f"%(self.sizeP[sourceNode])+"\nd+=%.3f"%(self.outDegP[sourceNode])
				subrank+=1
					
		return True
		
	def redraw(self):
		viewColor = self.qsg.getColorProperty("viewColor")
		viewSize = self.qsg.getSizeProperty("viewSize")
		viewLabel = self.qsg.getStringProperty("viewLabel")
		for n in self.qsg.getNodes():
			if not self.qsg.isMetaNode(n):
				viewSize[n] = tlp.Size(3,3,0)
				viewColor[n] = tlp.Color(255, 0, 0, 255)
			else:
				#print "meta"
				viewSize[n] = tlp.Size(3,3,0)
				
				
		for e in self.qsg.getEdges():
			viewSize[e] = tlp.Size(3,3,3)
			viewColor[e] = tlp.Color(0,0,255, 100)
		
		backup = self.qsg.getSuperGraph().addSubGraph()
		backup.setName("4.ranked")
		#tlp.copyToGraph(backup, self.qsg)
		for n in self.qsg.getNodes():
			backup.addNode(n)
		for e in self.qsg.getEdges():
			backup.addEdge(e)
			
		drawGraph = self.qsg.getSuperGraph().addSubGraph()
		drawGraph.setName("5.shape")
		#tlp.copyToGraph(drawGraph, self.qsg)
		for n in self.qsg.getNodes():
			drawGraph.addNode(n)
		for e in self.qsg.getEdges():
			drawGraph.addEdge(e)
		
		#drawGraph = self.qsg.addCloneSubGraph()
		#drawGraph.setName("shape")
		viewLayout = drawGraph.getLocalLayoutProperty("viewLayout")
		viewShape = drawGraph.getLocalIntegerProperty("viewShape")
		viewBorderWidth = drawGraph.getLocalDoubleProperty("viewBorderWidth")
		viewBorderColor = drawGraph.getLocalColorProperty("viewBorderColor")
		 
		rToN = {}
		for n in drawGraph.getNodes():
			r = self.roundP[n]
			if r not in rToN:
				rToN[r] = []
			rToN[r].append(n)
		
		rList = sorted(rToN.keys())
		delta = 6
		for r in rList:
			nList = sorted(rToN[r], key=lambda x: self.turnP[x])
			yPos = r*delta
			xLen = (len(nList)+1)/2.0
			for i in range(len(nList)):
				n = nList[i]
				xPos = delta * (i - xLen)
				viewLayout[n] = tlp.Coord(xPos, yPos, 0)
		
		overlay = False
		if overlay:		
			for r in rList:
				nList = sorted(rToN[r], key=lambda x: viewLabel[x])
				width = delta * (len(nList))
				height = delta
				yMin = height - delta/2.0
				yMax = height + delta/2.0
				xMin = -width/2.0
				xMax = width/2.0
				fillN = drawGraph.addNode()
				viewColor[fillN] = tlp.Color(0,255,0)
				viewShape[fillN] = 1
				viewSize[fillN] = tlp.Size(width,height,0)
				viewLayout[fillN] = tlp.Coord(-delta,r*delta,-1)
				viewBorderWidth[fillN] = 0.0
				viewBorderColor[fillN] = tlp.Color(0,255,0)
		
		self.drawGraph(drawGraph)

		
		dGraph = drawGraph.getSuperGraph().addSubGraph()
		dGraph.setName("6.shape")

		viewLayout2 = dGraph.getLocalLayoutProperty("viewLayout")
		viewShape2 = dGraph.getLocalIntegerProperty("viewShape")
		viewBorderWidth2 = dGraph.getLocalDoubleProperty("viewBorderWidth")
		viewBorderColor2 = dGraph.getLocalColorProperty("viewBorderColor")

		#tlp.copyToGraph(drawGraph, self.qsg)
		for n in drawGraph.getNodes():
			dGraph.addNode(n)
			c = viewLayout[n]
			viewLayout2[n] = tlp.Coord(c[0], c[1], c[2])
			viewShape2[n] = viewShape[n]
			viewBorderWidth2[n] = viewBorderWidth[n]
			viewBorderColor2[n] = viewBorderColor[n]
		for e in drawGraph.getEdges():
			dGraph.addEdge(e)
		
		rank2n = {}
		for n in dGraph.getNodes():
			r = self.roundP[n]
			if r not in rank2n:
				rank2n[r] = []
			rank2n[r].append(n)
			
		sortedRanks = sorted(rank2n.keys())
		
		for r in sortedRanks:
			for n in rank2n[r]:
				r2n = {}
				for e in dGraph.getOutEdges(n):
					n2 = dGraph.opposite(e, n)
					r2 = self.roundP[n2]
					if r2 not in r2n:
						r2n[r2] = []
					r2n[r2].append(e)
				rList = sorted(r2n.keys())
				if rList:
					rList.pop(0)
				for r2 in rList:
					eList = r2n[r2]
					for e in eList:
						dGraph.delEdge(e)
		
		self.drawGraph(dGraph)		
				
							

	def drawGraph(self, sg):
		#for e in sg.getEdges():
		#	sg.reverse(e)
			
		viewLabel = sg.getLocalStringProperty("viewLabel")
		typeName = sg.getStringProperty("typeName")
		#viewSize = sg.getLocalSizeProperty("viewSize")			
		#viewLayout = sg.getLocalLayoutProperty("viewLayout")
		#viewColor = sg.getLocalColorProperty("viewColor")
		
		for n in sg.getNodes():
			viewLabel[n] = typeName[n]
			if sg.isMetaNode(n):
				metagraph = sg.getNodeMetaInfo(n)
				typeNameM = metagraph.getStringProperty("typeName")
				newLabel = [typeNameM[m] for m in metagraph.getNodes()]
				viewLabel[n] = ("\n".join(newLabel)).encode("utf-8")
			#viewSize[n] = tlp.Size(1,1,0)
			
		#sg.computeLayoutProperty("FM^3 (OGDF)", viewLayout)
		#sg.computeLayoutProperty("Fast Overlap Removal",viewLayout)
		
			

# For later purpose, just keep reusing subgraph 3.meta

def main(graph):
	current = graph.getSuperGraph().addSubGraph()#
	current.setName("theShapeOfWords")
	tlp.copyToGraph(current, graph)		
	AT = DAGTrans(current)
	AT.computeDirectedGraph(True)
