from collections import deque, defaultdict
from heapq import *
import networkx as nx 
import osmnx as ox 
import requests  
# G = ox.graph_from_place('Piedmont, California, USA', network_type='walk')
#org, dst = (37.826003, -122.23309), (37.817440, -122.250660)
#org, dst = (42.346740, -72.512180), (42.395160, -72.531190) Boulders, CICS

org, dst = (37.825927, -122.232999), (37.826385, -122.238825) 
G = ox.graph_from_point(org, distance=900, simplify = False)
bbox = ox.bbox_from_point(org, distance=900)


G = ox.add_node_elevations(G, api_key="")
G = ox.add_edge_grades(G)

G_proj = ox.project_graph(G)
origin = ox.get_nearest_node(G, org, return_dist = True)
dest = ox.get_nearest_node(G, dst, return_dist = True)
if origin[1] > 100 or dest[1] > 100:
    raise ValueError("Nearest nodes found are inaccurate!!")

r = nx.shortest_path(G_proj, source=origin[0], target=dest[0], weight='length')
shortest = sum(ox.get_route_edge_attributes(G_proj, r, 'length'))

def printPath(parent, dest):
    "returns the shortest path given a parent mapping and the final dest"
    path = [dest]
    curr = parent[dest]
    while curr!=-1:
        path.append(curr)
        curr = parent[curr]
    return path[::-1]

#https://gist.github.com/kachayev/5990802
def dijkstra(src, target, xPercent, mode="increase"):
    q, seen, mins = [(0.0, 0.0, src)], set(), {src: 0}
    parent = defaultdict(int)
    parent[src] = -1
    while q:
        currElevDist, currDist, node = heappop(q)
        
        if node not in seen:
            seen.add(node)
            if node == target:
                return currDist, currElevDist, parent

            for nei in G.neighbors(node):
                if nei in seen: continue
                prev = mins.get(nei, None)
		length = getCost(node, nei)
		if mode == "increase":
            next = length - getCost(node, nei, "elevation-diff")
		else:
		    next = length + getCost(node, nei, "elevation-diff")
                nextDist = currDist + length
                if nextDist < shortest*(1.0+xPercent) and (prev is None or next < prev):
                    parent[nei] = node
                    mins[nei] = next
                    heappush(q, (next, nextDist, nei))

    return float("inf")

def hillClimbing(src, currDist, currElevDist, path, target, k, best):
        
    if currDist > shortest*(1.0+x):
        return
    
    if src == target:
        if normal : 
            if best[0][1] > currDist:
                best[0] = [currElevDist, currDist]
                best[1] = path[:]
        
        else:
            if best[0][0] < currElevDist:
                best[0] = [currElevDist, currDist]
                best[1] = path[:]
        return
    
    visited.add(src)
    topk = [[getCost(src, nei, "elev"), nei] for nei in G.neighbors(src) if nei not in visited]
    topk.sort(reverse = True)
    topk = topk[:k]
    for cost, nei in topk:
        hillClimbing(nei, currDist + getCost(src, nei), currElevDist + cost, path + [nei], target, k, best)
    
    visited.remove(src)
    return

def computeElevs(route,mode="both"):
    total = 0
    piecewiseElevs = []
    for i in range(len(route)-1):
	if mode == "both":
	    diff = getCost(route[i],route[i+1],"elevation-diff")	
	elif mode == "gain-only":
	    diff = getCost(route[i],route[i+1],"gain-only")
	elif mode == "drop-only":
	    diff = getCost(route[i],route[i+1],"drop-only")
	total += diff
	piecewiseElevs.append(diff)    	
    return total, piecewiseElevs

def printElevs(route):
    for singleNode in route:
	print(G.nodes[singleNode]["elevation"])

#normal = 0
#visited = set()
#x = 10.0/100
#best = [[float("-inf"), float("inf")], []]
#dfs(origin[0], 0.0, 0.0, [origin[0]], dest[0], best)
#hillClimbing(origin[0], 0.0, 0.0, [origin[0]], dest[0], 2, best)
#costDist, costElev, parent = dijkstra(origin[0], dest[0])
#print(best)
xPercent = 0.5
absDiff = getCost(origin[0],dest[0],mode="elevation-diff")
print ("Shortest path:",r) 
print ("Elevation difference between source and destination:",absDiff)
#print ("Elevations of each node on the shortest path:")
#printElevs(r)
sTotal,sPiecewise = computeElevs(r,"both")
sGainTotal, sGainPiecewise = computeElevs(r,"gain-only")
print ("Piecewise elevations:",sPiecewise)
print ("Elevation total and gain total:",sTotal,sGainTotal)

# Dijkstra's stats
currDist, currElevDist, parent = dijkstra(origin[0], dest[0], xPercent, mode="increase")
route = printPath(parent, dest[0])
print ("**********************************************************")
print("Dijkstra's path:",route)
print("Shortest length:",shortest,"Dijkstras length:",currDist)
#print("Elevations of each node on Dijkstra's path:")
#printElevs(route)
dTotal,dPiecewise = computeElevs(route,"both")
dGainTotal, dGainPiecewise = computeElevs(route,"gain-only")
print("Piecewise elevations:",dPiecewise)
print("Elevation total and gain total:",dTotal,dGainTotal)

assert (currDist <= (1+xPercent)*shortest)