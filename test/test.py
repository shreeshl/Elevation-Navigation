import sys
# sys.path.insert(0, '..')
import osmnx as ox
import networkx as nx
from elenav.controller.settings import *
from elenav.controller.algorithms import *
from elenav.controller.server import create_geojson, create_data
from elenav.model.graph_model import *

def return_on_failure(value = ""):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                f(*args,**kwargs)
                print("====>Passed " + u"\u2713\n")
            except Exception as e:
                print(e)
                print("====>Failed " + u"\u2717\n")
        return applicator
    return decorate

#get_bounding_box
@return_on_failure("")
def test_get_bounding_box(start, end):
    model = Model()
    bbox = model.get_bounding_box(start, end)
    assert len(bbox) == 4
    assert all(isinstance(coord, float) for coord in bbox)

#get_graph
@return_on_failure("")
def test_get_graph(start, end):
    model = Model()
    G = model.get_graph(start, end)
    assert isinstance(G, nx.classes.multidigraph.MultiDiGraph)

@return_on_failure("")
def test_shortest_path(G):
    
    #TESTING ALGO CORRECTNESS

    def getSum(G, route, attribute):

        attribute_values = []
        for u, v in zip(route[:-1], route[1:]):
            data = G.get_edge_data(u, v)[attribute]
            attribute_values.append(data)
        return sum(attribute_values)

    source = 0
    target = 2
    shortestDist = 6.0
    highElev = 4.0
    highElevDist = 10.0
    x = 100.0 #in percentage
    
    shortest_path = [[], 0.0, float('-inf'), 0.0]
    dfs(G, source, target, shortest_path, shortestDist, x = x)
    assert shortest_path[1] == highElevDist
    assert shortest_path[2] == highElev

@return_on_failure("")
def test_create_geojson(location):
    json = create_geojson(location)
    assert isinstance(json, dict)
    assert all(k in ["properties", "type", "geometry"] for k in json.keys())

@return_on_failure("")
def test_create_data(start, end, x = 0, min_max = "maximize"):
    d = create_data(start, end, x, min_max)
    assert isinstance(d, dict)

@return_on_failure("")
def test_getCost(G, n1 = 0, n2 = 1):
    
    c = getCost(G, 0, 1, mode = "normal")
    assert isinstance(c, float)
    assert c == 3.0
    
    c = getCost(G, 0, 3, mode = "elevation-diff")
    assert isinstance(c, float)
    assert c == 1.0
    
    c = getCost(G, 0, 3, mode = "gain-only")
    assert isinstance(c, float)
    assert c == 1.0
    
    c = getCost(G, 6, 2, mode = "drop-only")
    assert isinstance(c, float)
    assert c == 4.0
    
    c = getCost(G, 2, 6, mode = "drop-only")
    assert isinstance(c, float)
    assert c == 0.0

    c = getCost(G, 2, 6, mode = "abs")
    assert isinstance(c, float)
    assert c == 4.0

    c = getCost(G, 6, 2, mode = "abs")
    assert isinstance(c, float)
    assert c == 4.0

@return_on_failure("")
def test_computeElevs(G):
    route = [0, 6, 2]
    c, p = computeElevs(G, route, mode = "both")
    assert isinstance(c, float)
    assert isinstance(p, list)
    assert c == 0.0
    assert p == [4.0, -4.0]

    c, p = computeElevs(G, route, mode = "gain-only")
    assert isinstance(c, float)
    assert isinstance(p, list)
    assert c == 4.0
    assert p == [4.0, 0.0]

    c, p = computeElevs(G, route, mode = "drop-only")
    assert isinstance(c, float)
    assert isinstance(p, list)
    assert c == 4.0
    assert p == [0.0, 4.0]

@return_on_failure("")
def test_getRoute():
    c = getRoute({0 : 1, 1 : 2, 2 : -1}, 0)
    assert isinstance(c, list)
    assert c == [2, 1, 0]


if __name__ == "__main__":
    start, end = (42.373222, -72.519852), (42.375544, -72.524210)
    
    G = nx.Graph()
    [G.add_node(i, elevation = 0.0) for i in range(7)]
    edgeList = [(0,1,3.0), (1,2,3.0), (0,3,1.414), (3,4,4.0), (4,2,1.313), (0,5,4.24), (5,2,4.24), (0,6,5.0), (6,2,5.0)]
    G.add_weighted_edges_from(edgeList)
    elev = [0.0, 0.0, 0.0, 1.0, 1.0, 3.0, 4.0]

    for i, e in enumerate(elev):
        G.node[i]["elevation"] = e
    
    A = Algorithms(G)

    print("====>Testing get_bounding_box")
    test_get_bounding_box(start, end)
    print("====>Testing get_graph")
    test_get_graph(start, end)
    print("====>Testing get_shortest_path")
    test_shortest_path(G)
    print("====>Testing create_geojson")
    test_create_geojson(start)
    print("====>Testing create_data")
    test_create_data(start, end)
    print("====>Testing getCost")
    test_getCost(G)
    print("====>Testing computeElevs")
    test_computeElevs(G)
    print("====>Testing getRoute")
    test_getRoute()
