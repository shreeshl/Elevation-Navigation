import osmnx as ox
import networkx as nx
import numpy as np
import pickle as p
import os
import config

class Router:
    def __init__(self):
        print("Initialized")
        
        self.GOOGLEAPIKEY=config.API["googleapikey"]
        if os.path.exists("./graph.p"):
            self.G = p.load( open( "graph.p", "rb" ) )
            self.init = True
            print("Loaded Graph")
        else:
            self.init = False

    def get_bounding_box(self,start_location,end_location,distance=2000):
        """
        Returns the bounding box (N,S,E,W) given the start and end coordinates.

        Params:
            start_location: tuple (lat,long)
            end_location: tuple (lat,long)
            distance: Additional width given to the bbox at the corners(in metres)
        Returns:
            bbox: tuple (n,s,e,w)
        """
        bbox1=ox.bbox_from_point(start_location, distance)
        bbox2=ox.bbox_from_point(end_location, distance)
        bbox=(max(bbox1[0],bbox2[0]),min(bbox1[1],bbox2[1]),max(bbox1[2],bbox2[2]),min(bbox1[3],bbox2[3]))
        
        return bbox

    def get_shortest_path(self,start_location,end_location):
        """
        Returns the route(list of nodes) that minimiz the number of edges between the start and end location. 

        Params:
            start_location: tuple (lat,long)
            end_location: tuple (lat,long)
        Returns:
            lat_longs: List of [lon,lat] in the route
        """
        if not self.init:
            # bbox=self.get_bounding_box(start_location,end_location)
            # self.G = ox.graph_from_bbox(bbox[0],bbox[1],bbox[2],bbox[3],network_type='walk', simplify=False)
            self.G = ox.graph_from_point(start_location, distance=10000, simplify = False, network_type='walk')
            p.dump( self.G, open( "graph.p", "wb" ) )
            self.init = True
            print("Saved Graph")
        
        G = self.G
        start_node=ox.get_nearest_node(G, point=start_location)
        end_node=ox.get_nearest_node(G, point=end_location)
        route = nx.shortest_path(G, start_node, end_node)        
        lat_longs=[[G.node[route_node]['x'],G.node[route_node]['y']] for route_node in route ]        
        return lat_longs
    
    def get_graph_with_elevation(self,bbox):
        """
        Returns networkx graph G with eleveation data appended to each node and rise/fall grade to each edge.

        Params:
            bbox:tuple (n,s,e,w)
        Returns:
            G: networkx graph
        """
        G = ox.graph_from_bbox(bbox[0],bbox[1],bbox[2],bbox[3],network_type='drive')        
        G = ox.add_node_elevations(G, api_key=self.GOOGLEAPIKEY)        

        return G
    
    def distance_between_locs(self,lat1,lon1,lat2,lon2):
        """
        Return the distance between two locations given the lat/long's.
        """
        R=6371008.8 #radius of the earth
        
        lat1 = np.radians(lat1)
        lon1 = np.radians(lon1)
        lat2 = np.radians(lat2)
        lon2 = np.radians(lon2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        distance = R * c
        return distance
        
    
    def add_dist_from_dest(self,G,end_location):
        """
        Adds distance from destination location to all the nodes in the graph
        Args:
        G : networkx multidigraph
        Returns
        G : networkx multidigraph
        """
        end_node=G.nodes[ox.get_nearest_node(G, point=end_location)]
        lat1=end_node["y"]
        lon1=end_node["x"]
        
        for node,data in G.nodes(data=True):
            lat2=G.nodes[node]['y']
            lon2=G.nodes[node]['x']
            distance=self.distance_between_locs(lat1,lon1,lat2,lon2)            
            data['dist_from_dest'] = distance
            
        return G

    
    def a_star(self,start_location,end_location):
        """
        Returns the route(list of nodes) that minimize change in elevation between start and end using the A* node, with the heuristic 
        being the distance from the end node. 
        Params:
            start_location: tuple (lat,long)
            end_location: tuple (lat,long)
         Returns:
            lat_longs: List of [lon,lat] in the route
        """
        if not self.init:
            # bbox=self.get_bounding_box(start_location,end_location)
            # self.G = ox.graph_from_bbox(bbox[0],bbox[1],bbox[2],bbox[3],network_type='walk', simplify=False)
            self.G = ox.graph_from_point(start_location, distance=10000, simplify = False, network_type='walk')
            p.dump( self.G, open( "graph.p", "wb" ) )
            self.init = True
            print("Saved Graph")
        
        G = self.G
        
        #Graph initialization
        bbox=self.get_bounding_box(start_location,end_location)
        G=self.get_graph_with_elevation(bbox)
        G=self.add_dist_from_dest(G,end_location)
        #Initialization of pre-reqs
        start_node=ox.get_nearest_node(G, point=start_location)
        end_node=ox.get_nearest_node(G, point=end_location)


        shortest_route = nx.shortest_path(G, source=start_node, target=end_node, weight='length')
        shortest_dist = sum(ox.get_route_edge_attributes(G, shortest_route, 'length'))
        def reconstruct_path(cameFrom, current):
            """
            Function to retrace the path from end node to start node. Returns in the format required by Mapbox API(for plotting)
            """
            total_path = [current]
            while current in cameFrom:
                current = cameFrom[current]
                total_path.append(current)
            ele_latlong=[[G.node[route_node]['x'],G.node[route_node]['y']] for route_node in total_path ] 
            shortest_latlong=[[G.node[route_node]['x'],G.node[route_node]['y']] for route_node in shortest_route ] 
            return (ele_latlong,shortest_latlong)        
        
        #The settotal_path of nodes already evaluated
        closedSet=set()
        # The set of currently discovered nodes that are not evaluated yet.
        # Initially, only the start node is known.        
        openSet=set()
        openSet.add(start_node)
        # For each node, which node it can most efficiently be reached from.
        # If a node can be reached from many nodes, cameFrom will eventually contain the
        # most efficient previous step.
        cameFrom={}
        #For each node, the cost of getting from the start node to that node.
        gScore={}
        for node in G.nodes():
            gScore[node]=float("inf")
        #The cost of going from start to start is zero.
        gScore[start_node] =0 
        # For each node, the total cost of getting from the start node to the goal
        # by passing by that node. That value is partly known, partly heuristic.
        fScore={}

        # For the first node, that value is completely heuristic.
        fScore[start_node] = 0#G.nodes[start_node]['dist_from_dest']

        

        while openSet!={}:
            current= min([(node,fScore[node]) for node in openSet],key=lambda t: t[1]) [0]            
            if current==end_node:
                return reconstruct_path(cameFrom, current)
            openSet.remove(current)
            closedSet.add(current)

            for neighbor in G.neighbors(current):
                if neighbor in closedSet:
                    continue # Ignore the neighbor which is already evaluated.
                #The distance from start to a neighbor
                tentative_gScore= gScore[current]+1/abs(G.nodes[current]['elevation'] - G.nodes[neighbor]['elevation'])
                if neighbor not in openSet:# Discover a new node
                    openSet.add(neighbor)
                else:
                    if tentative_gScore>=gScore[neighbor] :#Stop searching along this path if distance exceed 1.5 times shortest path
                        continue# This is not a better path.
                cameFrom[neighbor]=current
                gScore[neighbor]=tentative_gScore
                fScore[neighbor]=gScore[neighbor]# + G.nodes[neighbor]['dist_from_dest']


# r.get_shortest_path((42.377041, -72.519681),(42.350070, -72.528798))
# print(r.a_star((42.377041, -72.519681),(42.350070, -72.528798)))