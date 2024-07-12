# -*- coding: utf-8 -*-
"""Dijkstra_method.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ZyBJBraFM6gzHx7ix-Ga9xO2NtnObLdl
"""

import networkx as nx
import matplotlib.pyplot as plt
import random
from math import *
import numpy as np
import copy
import threading
import time
import scipy.stats
import pandas as pd
import itertools
from itertools import chain
from collections import Counter
import queue
from collections import defaultdict
from datetime import datetime


#logistic function for displaying the created networkx graph
def printGraph(gra):
  fig, ax = plt.subplots(figsize=(20, 10))
  posi = dict()
  for nds in range(gra.number_of_nodes()):
    posi[nds] = gra.nodes[nds]['pos'] #tupples (x,y)
  nx.draw(gra,posi, with_labels = True, **{'node_color' : 'orange', 'node_size' : 400})

#heuristic function for calculating the air-distance between two nodes in the snapshot of the network
def heuristicAirDistance(graph, node1, node2):
  airDist = np.linalg.norm(np.array(graph.nodes[node1]['pos'])-np.array(graph.nodes[node2]['pos']))
  return (airDist)

#function to initialise the reward and q-table
def rAndQs(graph, goalNode):
  n = graph.number_of_nodes()
  hW = 0.7

  #initialising the reward values for every state-action pair according to heuristic algorithm discussed in the paper
  global R
  R= np.zeros(shape = (n,n))
  for u in range(n) :
    for v in graph[u]:
      R[u][v] = (1/( hW*heuristicAirDistance(graph,v,goalNode) + (1-hW)*heuristicAirDistance(graph,u,v) ) )

  for v in graph[goalNode] :
    R[v][goalNode] = R[v][goalNode] + 100

  #Qtable initialisation
  global Q
  Q= np.zeros(shape = (n,n))
  Q -= 200
  for nds in range(n):
    for nbs in graph[nds]:
      Q[nds][nbs] = 0
      Q[nbs][nds] = 0

  return

#function to select the next state/action for a given state according to the exploration rate
def nextState(graph, startNode, exploreRate):
  #action following exploration
  if (random.random()<=exploreRate):
    sample = list(dict(graph[startNode]).keys())

  #action following exploitation
  else :
    sample = np.where(Q[startNode,] == np.max(Q[startNode,]))[0]

  nextNode = int(random.choice(sample))

  return nextNode

#function to update the Qtable for a given state-action pair
def updateQs(node1, node2, alpha, discount):
  #calculating the future discounted reward
  futureSample = np.where(Q[node2,] == np.max(Q[node2,]))[0]
  if futureSample.shape[0] > 1:
    futureNextState = int(random.choice(futureSample))
  else :
    futureNextState = int(futureSample)
  maxValue = Q[node2,futureNextState]

  #Updating the qtable according to the reinforcement learning algorithm explained in the paper
  Q[node1,node2] = ((1-alpha)*Q[node1,node2] + alpha*(R[node1,node2] + discount*maxValue))

#function that initialises and deploys the qlearning agent
def qLearnModel(graph, goalNode, exploreRate, alpha, discount):
  rAndQs(graph, goalNode)

  n = graph.number_of_nodes()

  #Training the qlearning agent for 80000 epochs
  for i in range(80000):
    start = random.randint(0,n-1)
    if len(graph[start]) >=1 :
      #setting the decaying learning rate
      alpha = alpha**(0.85 * (i//1000))
      nextNode = nextState(graph, start, exploreRate)
      updateQs(start, nextNode, alpha, discount)

  return Q



#Function that deploys the Dynamic LPWAN Network and also the qlearning agent on it to extract qtable for each snapshot of the graph
def FspatGraph(N, limit, goalNode = 0, distribution = "poisson", printGraph = True, embarkingNow = True, previousG = None, probOfMobilizing = 1.0, exploreRate = 0.5, alpha = 0.8, discount = 0.8):

  #Creating the network for the first snapshot of the network
  if embarkingNow == True :
    global spatG
    spatG = nx.Graph()
    points = []

    #creating the IoD nodes
    for nodes in range(N):
      points.append(nodes)
    #[0,1,2,3,4,5,6...,N-1]

    #setting the IoD nodes positions according to poisson distribution
    global pos
    pos = dict()

    for nd in range(N):
      if nd == goalNode :
        pos[nd] = [2000,2000]
      elif distribution == "random":
        pos[nd] = [random.uniform(0,300), random.uniform(0,300)]

      elif distribution == "normal":
        Mean = 0
        SD = 100
        pos[nd] = [Mean+np.random.normal(0,1)*SD, Mean+np.random.normal(0,1)*SD]
      elif distribution == "poisson":
        xMin, xMax, yMin, yMax = 0, 4000, 0, 4000
        xDelta=xMax-xMin
        yDelta=yMax-yMin
        areaTotal=xDelta*yDelta

        lambda0=2; #intensity (ie mean density) of the Poisson process
        xx = xDelta*scipy.stats.uniform.rvs(0,1, size =1 )+xMin#x coordinates of Poisson points
        yy = yDelta*scipy.stats.uniform.rvs(0,1, size = 1) +yMin#y coordinates of Poisson points

        pos[nd] = [*xx, *yy]  #unpacking of list xx and yy

      spatG.add_node(nd,pos = pos[nd])
      #1st snapshot

  else:
    #taking the node positions from previous snapshot of the network
    N = previousG.number_of_nodes()
    pos = dict()

    #determining the probability of mobility of IoD devices according to probability distribution
    shift = []
    for i in range(N):
      if i != goalNode :
        shift.append(random.random())
      else :
        shift.append(2)

    shift = [p<=probOfMobilizing for p in shift]
    previousG.remove_edges_from(previousG.edges())

    #determining the random position of the IoD in future snapshot within the radio range
    for nd in range(N):
      pos[nd] = previousG.nodes[nd]['pos']
      if shift[nd] == 1:
        previousX = previousG.nodes[nd]['pos'][0]
        previousY = previousG.nodes[nd]['pos'][1]

        newX = random.uniform(previousX-limit, previousX + limit)
        while newX >= 4000 :
          newX = random.uniform(previousX-limit, previousX + limit)

        yLowLimit = -1*( ( limit**2 - (newX-previousX)**2 )**0.5) + previousY  # "Y" coord should lie within circle of radius equal to limit.
        yHighLimit =  ( limit**2 - (newX-previousX)**2 )**0.5 + previousY
        newY = random.uniform( yLowLimit , yHighLimit )
        while newY >= 4000 :
          yLowLimit = -1*( ( limit**2 - (newX-previousX)**2 )**0.5) + previousY
          yHighLimit =  ( limit**2 - (newX-previousX)**2 )**0.5 + previousY
          newY = random.uniform( yLowLimit , yHighLimit )

        previousG.nodes[nd]['pos'] = [newX, newY]
        pos[nd] = [newX, newY]

    spatG = previousG

  dist = np.empty((N,N))

  #calculating changed distances and edge connections between the moves IoDs
  connects = []
  for u in range(dist.shape[0]):
    for v in range(dist.shape[1]):
      point1 = np.array(spatG.nodes[u]['pos'])
      point2 = np.array(spatG.nodes[v]['pos'])

      dist[u][v] = np.linalg.norm(point1-point2)
      dist[u][v] = (dist[u][v]<=limit)*dist[u][v]

      if dist[u][v] != 0:
        connects.append((u,v, dist[u][v])) # list of tupples --->  connects

  spatG.add_weighted_edges_from(connects)

  #Displaying the snapshot of the graph
  if printGraph == True :
    fig, ax = plt.subplots(figsize=(20, 10))
    nx.draw(spatG,pos, with_labels = True, **{'node_color' : 'orange', 'node_size' : 400})

  #Deploying and extracting the Qtable of each of the snapshot of the network
  qTable = qLearnModel(spatG, goalNode, exploreRate, alpha, discount)


  #storing the qtable values in individual nodes
  for nds in range(N):
    qChunk = {}
    for nbs in spatG[nds]:
      qChunk[nbs] = qTable[nds][nbs]

    spatG.nodes[nds]['qChunk'] =  qChunk


  for nds in range(N):
    alloted_queue = {}
    if nds == 0:
      max_ele = 20000
      alloted_queue[0] = queue.Queue(maxsize = max_ele)

    else:
      max_ele = 800
      alloted_queue[nds] = queue.Queue(maxsize = max_ele)

    spatG.nodes[nds]['alloted_queue'] =  alloted_queue

  # print(list(spatG.nodes[10]['alloted_queue'][10].queue))

  return spatG, pos, qTable

#################################################################### Graph Creation Ends Here ###########################################################################################


#Energy of all the IoDs are initialised
enen=[]
enee=[]
for i in range(400):
  enen.append(i)
  enee.append(0)
ene=dict(zip(enen,enee))
for i in ene:
  ene[i]=72000
ene[0]=10000000

#function to determine the shortestpath calculation
def shortestPath1(graph, QTable, sourceNode, goalNode, cords, exploreRate=0.5, alpha=0.8, discount=0.8):

  #looking up the learned qtable for each snapshot of the network
  qTable = copy.deepcopy(QTable)
  count = 0
  tolerance = 0
  #performing the shortest path search algorithm according the residual energies of the IoD devices
  if ene[sourceNode]>1:
    path = [sourceNode]
  else:
    return [], qTable

  nextNode = np.argmax(qTable[sourceNode,])
  tic = time.time()
  toc = tic

  db = round(((sqrt(((cords[sourceNode][0]-cords[nextNode][0])**2)+((cords[sourceNode][1]-cords[nextNode][1])**2) ))),2)

  startEngDeduction = 0
  while nextNode != goalNode :

    #Condition when qtable and the residual energies of the nodes both support q-learning algorithm
    if nextNode not in path and ene[nextNode] >1:

      path.append(nextNode)
      db = round(((sqrt(((cords[path[-2]][0]-cords[nextNode][0])**2)+((cords[path[-2]][1]-cords[nextNode][1])**2) ))),2)
      startEngDeduction = 1

      #deducing the energy of transmission according to distance models
      if db<=520 and startEngDeduction != 0:
          e=0.3256*pow(10,-3)+(0.000041*pow(db,2))
          ene[path[-2]]=ene[path[-2]]-e

      elif db>520 and startEngDeduction != 0:
          e=0.3256*pow(10,-3)+((2*pow(10,-10)*pow(db,4)))
          ene[path[-2]]=ene[path[-2]]-e

      nextNode = np.argmax(qTable[nextNode,])

    #Condition when qtable best node can't be used due to low residual energy, then the next best node until 3 or less attempts is tried out
    elif (nextNode in path and tolerance == 0) or (ene[nextNode] <=1 and tolerance == 0) :
      count = 0
      while count < min(4,len(graph[path[-1]])-1) :
        count += 1
        if count == 1 :
          qChunk = {}
          for nbs in graph[path[-1]]:
            qChunk[nbs] = qTable[path[-1]][nbs]
          listOfQmax = sorted(qChunk.items(), key=lambda item: item[1], reverse = True)
          listOfQmax = [t[0] for t in listOfQmax]  #separating keys

        #chosing the next best node with required residual energy
        if ene[listOfQmax[count]]>1:
          nextNode = listOfQmax[count]

        #if next node has energy make it the next node
        if nextNode not in path and ene[nextNode] >1 :
          break
      #if no suitable IoD is selected after 3 attempts tolerance is lost and direct hop is executed
      if count >= 4 or count >= len(graph[path[-1]])-1:
        tolerance = 1

    #condition for executing a direct hop transmission
    elif (nextNode in path and tolerance == 1) or (ene[nextNode] <=1 and tolerance == 1):
      #path.append("--Kinked path to-- ")
      db = round(((sqrt(((cords[path[-1]][0]-cords[0][0])**2)+((cords[path[-1]][1]-cords[0][1])**2) ))),2)
      if db<=520 :
          e=0.3256*pow(10,-3)+(0.000041*pow(db,2))
          ene[path[-1]]=ene[path[-1]]-e

      else:
          e=0.3256*pow(10,-3)+(2*pow(10,-10)*pow(db,4))
          ene[path[-1]]=ene[path[-1]]-e

      break

  path.append(goalNode)

  return path, qTable


#logistic function to find the best exploration rate

def shortestPathConclusion(graph, sourceNode, goalNode, alpha, discount):
  sps = []
  spls =[]
  qtables = []
  exploreRates = [0.0 + i/10 for i in range(10)]

  for exploreRate in exploreRates :
    sp, qtable= shortestPath1(graph, sourceNode, goalNode, exploreRate, alpha, exploreRate)
    sps.append(sp)
    qtables.append(qtable)
    length = 0
    for i in range(len(sp)-1):
      if type(sp[i+1]) == type("str") :
        length = float('inf')
        break
      length += graph[sp[i]][sp[i+1]]['weight']
    spls.append(length)

  print("\nAll experimented paths : ", sps)
  return sps[spls.index(min(spls))], qtables[spls.index(min(spls))]

#-------------------------------------------------------------------------------------------------------------------/////////////////////////////////////////////-------------------------------
#-------------------------------------------------------------------------------------------------------------------/////////////////////////////////////////////-------------------------------


def dijkstra(graph, start, goal):
    import heapq
    queue = [(0, start)]
    shortest_paths = {start: (None, 0)}

    while queue:
        (cost, node) = heapq.heappop(queue)
        if node == goal:
            break

        for neighbor in graph[node]:
            old_cost = shortest_paths.get(neighbor, (None, float('inf')))[1]
            new_cost = cost + graph[node][neighbor]['weight']
            if new_cost < old_cost:
                shortest_paths[neighbor] = (node, new_cost)
                heapq.heappush(queue, (new_cost, neighbor))

    if goal not in shortest_paths:
        return [], float('inf')

    path = []
    while goal is not None:
        path.append(goal)
        next_node = shortest_paths[goal][0]
        goal = next_node

    path.reverse()
    return path, shortest_paths[path[-1]][1]

#-------------------------------------------------------------------------------------------------------------------/////////////////////////////////////////////-------------------------------
#-------------------------------------------------------------------------------------------------------------------/////////////////////////////////////////////-------------------------------


################################################################# Functions Related To Shortest Path End Here #########################################################################


# without RTS-CTS -----------------------------------------------

def is_queue_full(graph, node_id):
    queue_of_node = graph.nodes[node_id]['alloted_queue'][node_id]
    return queue_of_node.full()

def is_queue_empty(graph, node_id):
    queue_of_node = graph.nodes[node_id]['alloted_queue'][node_id]
    return queue_of_node.empty()

def transmit_data(graph,current_node, next_node, data):
    timing = 0
    tic = time.time()
    # print(f"before {current_node} ------>> {len(list(graph.nodes[current_node]['alloted_queue'][current_node].queue))}")
    list_of_data_current_node = graph.nodes[current_node]['alloted_queue'][current_node]
    put_data = list_of_data_current_node.get()


    # print(f"after {current_node} <<------ {len(list(graph.nodes[current_node]['alloted_queue'][current_node].queue))}")

    # print(f"before {next_node} ------>>  {len(list(graph.nodes[next_node]['alloted_queue'][next_node].queue))}")
    if graph.nodes[next_node]['alloted_queue'][next_node].full() == False:
      graph.nodes[next_node]['alloted_queue'][next_node].put(put_data)

    # print(f"after {next_node} <<------  {len(list(graph.nodes[next_node]['alloted_queue'][next_node].queue))}")
    # print(f"Node {current_node} transmittED data to {next_node}\n")
    toc = time.time()
    timing = toc-tic
    return timing


def simulate_sensor_readings():
    # Simulate temperature and humidity readings
    temperature = 20 + random.gauss(0, 5)  # Mean temperature around 20°C with some noise
    humidity = 50 + random.gauss(0, 10)  # Mean humidity around 50% with some noise
    return temperature, humidity

def get_time_of_day_factor():
    # Simulate time of day factor (day: 1, night: 0.5)
    hour = datetime.now().hour
    return 1 if 6 <= hour < 18 else 0.5

def get_battery_level():
    # Simulate battery level between 20% and 100%
    return 20 + random.random() * 80

def get_proximity_to_events():
    # Simulate proximity to events (closer: higher value)
    return random.random()

def get_weather_condition():
    # Simulate different weather conditions (clear: 1, rainy: 0.8, foggy: 0.6)
    weather_conditions = {'clear': 1, 'rainy': 0.8, 'foggy': 0.6}
    return weather_conditions[random.choice(list(weather_conditions.keys()))]

def get_node_health():
    # Simulate node health (good: 1, degraded: 0.7, bad: 0.4)
    health_status = {'good': 1, 'degraded': 0.7, 'bad': 0.4}
    return health_status[random.choice(list(health_status.keys()))]

def get_movement_vibration():
    # Simulate movement or vibration (no: 1, slight: 1.2, high: 1.5)
    movement_status = {'no': 1, 'slight': 1.2, 'high': 1.5}
    return movement_status[random.choice(list(movement_status.keys()))]

def get_node_density():
    # Simulate node density (few neighbors: 1, moderate: 0.9, high: 0.8)
    density_status = {'few': 1, 'moderate': 0.9, 'high': 0.8}
    return density_status[random.choice(list(density_status.keys()))]

def generate_data_based_on_conditions(temperature, humidity, time_of_day, battery_level, proximity, weather, health, movement, density):
    base_count = 50

    # Adjust base count based on conditions
    base_count *= time_of_day
    base_count *= (battery_level / 100)
    base_count *= (1 + proximity)
    base_count *= weather
    base_count *= health
    base_count *= movement
    base_count *= density

    # Further adjust based on temperature and humidity
    if temperature > 25 and humidity > 60:
        base_count *= 1.25
    elif temperature > 20 and humidity > 50:
        base_count *= 1.1

    return int(base_count)



global ls_tx, ls_rx,tpp,tpd
tpp = []
tpd = []
ls_rx =[]
ls_tx =[]
Gpath = {}
gen_data = []

#function to execute the dynamic LPWAN as a whole for a totalDuration's time
def executeSimulation(NumberOfNodes, radioRange, probabilityOfMobilizing, totalDuration):

  global figCount
  figCount = 1
  listOfGraphs =[]
  timingToGraph = 0

  while  timingToGraph <= totalDuration:
    tic = time.time()
    if figCount == 1:

      spatGraph,positions,qTable = FspatGraph(NumberOfNodes,radioRange, printGraph = False) #Any function

    else :

      spatGraph,positions,qTable = FspatGraph(_,radioRange, printGraph = False, embarkingNow= False, previousG= spatGraph, probOfMobilizing= probabilityOfMobilizing)

    toc = time.time()
    timingToGraph += toc-tic



#------------------------------------------------------------------------------------------///////////////////////////////////////////-------------------
#------------------------------------------------------------------------------------------///////////////////////////////////////////-------------------



    def calculate_throughput(graph, path):
      if not path or len(path) < 2:
        return 0
      total_weight = sum(heuristicAirDistance(graph, path[i], path[i+1]) for i in range(len(path)-1))
      return 1 / total_weight if total_weight != 0 else float('inf')


    tpp1 = []
    tpd1 = []
    def compare_throughput(graph, q_table, start, goal):

        # Q-learning based shortest path
        q_path, _ = shortestPath1(graph, q_table, start, goal, positions)
        q_throughput = calculate_throughput(graph, q_path)
        tpp1.append(q_throughput)

        # Dijkstra's shortest path
        dijkstra_path, _ = dijkstra(graph, start, goal)
        dijkstra_throughput = calculate_throughput(graph, dijkstra_path)
        tpd1.append(dijkstra_throughput)

        print("Q-learning based shortest path:", q_path)
        print("Q-learning throughput:", q_throughput)
        print("Dijkstra's shortest path:", dijkstra_path)
        print("Dijkstra's throughput:", dijkstra_throughput)

        print(f"q_throughput = {q_throughput} ----- dijkstra_throughput = {dijkstra_throughput}")

    # Example of comparing throughputs
    for node in range(1,400):
      print(compare_throughput(spatGraph, qTable, node, 0))
    # print(tpp1)
    # print(tpd1)
#------------------------------------------------------------------------------------------///////////////////////////////////////////-------------------
#------------------------------------------------------------------------------------------///////////////////////////////////////////-------------------


#-----------------------------------------------------------------------------
    for nds in range(1,NumberOfNodes):

      temperature, humidity = simulate_sensor_readings()
      time_of_day = get_time_of_day_factor()
      battery_level = get_battery_level()
      proximity = get_proximity_to_events()
      weather = get_weather_condition()
      health = get_node_health()
      movement = get_movement_vibration()
      density = get_node_density()

      no_of_data = generate_data_based_on_conditions(temperature, humidity, time_of_day, battery_level, proximity, weather, health, movement, density)
      if no_of_data > 40:
        no_of_data = 40
      if no_of_data < 1:
        no_of_data = 1

      for i in range(no_of_data):
        spatGraph.nodes[nds]['alloted_queue'][nds].put(f"Node{nds}")

#-----------------------------------------------------------------------------
    spath={}
    for nds in range(400):
      if nds == 0 :
        continue
      if len(spatGraph[nds]) >=1 :
        # sp,_ = shortestPath1(spatGraph, qTable, nds, 0, positions) # exploreRate=0.5, alpha = 0.8, discount =0.8)
        sp,_ = dijkstra(spatGraph, nds, 0)

        if len(sp)>1:
          spath[nds] =sp

    Gpath[figCount-1] = spath
    #Gpath = {0:{0:[], 1:[],  2:[]}, 1:{0:[], 1:[], 2:[]}, 2:{0:[], 1:[], 2:[]}}

    eligible_nodes = []
    eligible_nodes.append(list(spath.keys()))
    # print(eligible_nodes)

#----------------------------------------------^^^^^^^^^^^^^^^^-------------------------
    temp_queues = {}
    for nd in spatGraph.nodes:
      temp_queues[nd] = spatGraph.nodes[nd]['alloted_queue']
      del spatGraph.nodes[nd]['alloted_queue']

    gra, graPos,graQt  = copy.deepcopy(spatGraph),copy.deepcopy(positions),copy.deepcopy(qTable)

    for nd in spatGraph.nodes:
        spatGraph.nodes[nd]['alloted_queue'] = temp_queues[nd]

    listOfGraphs.append([gra, graPos, graQt])
#----------------------------------------------------------------------------

    tx_data = 0
    for nds in range(400):
      tx_data += len(list(spatGraph.nodes[nds]['alloted_queue'][nds].queue))

    for nds in range(1,400):
      print(list(spatGraph.nodes[nds]['alloted_queue'][nds].queue))
    gen_data.append(tx_data)
#-----------------------------------------------------------------------

    # remaining_data = 0
    received = 0
    timing= 0

    while timing<=(toc-tic) : # and timing < 0.07  # is_queue_full(spatGraph,0) == False and remaining_data > 0 and timing<= (toc-tic)

      nodes_having_data = []
      for nds in range(1,400):
        if nds in eligible_nodes[0]:
          if is_queue_empty(spatGraph,nds) == False:
            nodes_having_data.append(nds)


      received = len(list(spatGraph.nodes[0]['alloted_queue'][0].queue))
      print(f"\n--------->> {len(list(spatGraph.nodes[0]['alloted_queue'][0].queue))} <<----- data in Goal node.------>> {tx_data} <<-----Total data-------Graphs = {figCount}\n")
      print(nodes_having_data)
      if len(nodes_having_data)>0:
        select_node = random.choice(nodes_having_data)
        nextNode = spath[select_node][1]
      else:
        break

      timing += transmit_data(spatGraph,select_node,nextNode, f"Data to {nextNode}")


    ls_tx.append(timing)
    print("\n\nDONE..!")
    print(f"--------->> {len(list(spatGraph.nodes[0]['alloted_queue'][0].queue))} <<------data in Goal node.----->> {tx_data} <<-----Total data")
    ls_rx.append(len(list(spatGraph.nodes[0]['alloted_queue'][0].queue)))

  #-----------------------------------------------^^^^^^^^^^^^^^^^^^^-------------------------
    remaining_data = 0
    for nds in range(1,400):
      remaining_data += len(list(spatGraph.nodes[nds]['alloted_queue'][nds].queue))
    print(remaining_data)

    for nds in range(400):
      print(list(spatGraph.nodes[nds]['alloted_queue'][nds].queue))

    print(ls_rx)
    print(ls_tx)
    print(gen_data)
    print("\n\n")
    figCount += 1

    tpp.append(tpp1)
    tpd.append(tpd1)
#----------------------------------------------------------------------------

  print("Stats :\n")
  print("\nTotal duration of the simulation set : ", totalDuration)
  print("\nTotal duration of time simulation used : ", toc-tic)
  print("\nTime taken per one screen shot of network : ", (toc-tic)/(len(listOfGraphs)))
  print("\nTotal output screen shots generated : ", len(listOfGraphs))
  print(tpp)
  print(tpd)
  # print(list(spatG.nodes[10]['alloted_queue'][10].queue))
  print("\n\n")

  return listOfGraphs


Graphs = executeSimulation(400,520 , 0.4, 40)    #(400,520 , 0.4, 1000)

# [592, 588, 587, 586, 526, 519, 494, 473, 472, 453, 442, 436, 432, 426, 423, 417, 416, 410, 407, 404, 398, 394, 391, 387, 384, 379, 375, 372, 365, 363, 358, 357, 351, 347, 344, 340, 339, 337, 330, 327, 324, 323, 320, 315, 311, 307, 307, 302, 301, 297, 291, 291, 288, 286, 281, 278, 277, 273, 272, 268, 265, 262, 261, 256, 255, 251, 247, 245, 245, 240, 239, 237, 234, 230, 231, 230, 231, 229, 226, 226, 221, 221, 218, 215, 213, 212, 208, 208, 206, 203, 202, 197, 196, 196, 194, 192, 189, 189, 184, 183, 181, 180, 177, 175, 173, 172, 171, 169, 166, 166, 165, 163, 162, 158, 156, 157, 153, 155, 152, 151, 150, 149, 146, 144, 142, 141, 140, 141, 136, 136, 136, 132, 134, 130, 131, 128, 125, 124, 123, 122, 120, 121, 118, 119, 117, 117, 114, 112, 113, 110, 112, 108, 108, 106, 107, 106, 103, 101, 102, 101, 100, 97, 98, 96, 94, 96, 94, 93, 94, 91, 89, 87, 90, 88, 86, 88, 85, 86, 84, 83, 82, 79, 80, 81, 79, 77, 79, 78, 74, 74, 74, 73, 74, 70, 69, 68, 70, 70, 68, 65, 67, 66, 65, 65, 63, 64, 61, 62, 62, 61, 60, 60, 60, 57, 56, 58, 58, 57, 54, 53, 53, 54, 52, 54, 54, 53, 53, 51, 49, 48, 47, 47, 47, 48]

print(ls_rx)
print(ls_tx)
print(gen_data)