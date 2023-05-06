import sys
import heapq

city_id = {}
id_city = {}
trans_id = {}
id_trans = {}

class Graph:
	def __init__(self):
		self.edges = {}

	def add_edge(self, from_city, to_city, transport_type, cruise_time, cruise_fare):
		if from_city not in self.edges:
			self.edges[from_city] = {}
		self.edges[from_city][(to_city, transport_type)] = (cruise_time, cruise_fare)

	def get_edge(self, from_city, to_city, transport_type):
		if from_city in self.edges and (to_city, transport_type) in self.edges[from_city]:
			return self.edges[from_city][(to_city, transport_type)]
		return None


'''
# Функция для добавления ребер в граф
def add_edge(from_city, to_city, transport_type, cruise_time, cruise_fare):
    # Проверяем, есть ли уже данный город в словаре graph
    if from_city not in graph:
        graph[from_city] = {}
    if to_city not in graph:
        graph[to_city] = {}
    # Добавляем ребро от города отправления к городу прибытия
    graph[from_city][to_city] = (transport_type, cruise_time, cruise_fare)
'''

def read_graph_from_file(file_path):
	graph = Graph()
	with open(file_path, "r") as f:
		city_number = 0
		trans_number = 0
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			parts = line.split()
			if len(parts) != 5:
				continue
			from_city, to_city, transport_type = parts[0], parts[1], parts[2]
			cruise_time, cruise_fare = int(parts[3]), int(parts[4])
			graph.add_edge(from_city, to_city, transport_type, cruise_time, cruise_fare)
			#add_edge(from_city, to_city, transport_type, cruise_time, cruise_fare)
			if (transport_type not in trans_id):
				trans_id[transport_type] = trans_number
				id_trans[trans_number] = transport_type
				trans_number += 1
			
			if (from_city not in city_id): 
				city_id[from_city] = city_number
				id_city[city_number] = from_city
				city_number += 1
			
			if (to_city not in city_id): 
				city_id[to_city] = city_number
				id_city[city_number] = to_city
				city_number += 1
	return graph

if __name__ == "__main__":
	file_path = sys.argv[1]
	graph = read_graph_from_file(file_path)
	print(graph.edges)
	print(city_id)
	print(trans_id)
	
	print("Введите город отправления: ")
	start_city = input()
	flag_1 = False
	while flag_1 == False:
		first_city = f'\"{start_city}\"'
		if first_city in city_id:
			flag_1 = True
		else:
			print('takogo goroda net, vvedite noviy gorod otpravlenia')
			start_city = input()
		
	print("Введите город прибытия: ")
	exit_city = input()
	flag_2 = False
	while flag_2 == False:
		second_city = f'\"{exit_city}\"'
		if second_city in city_id:
			flag_2 = True
		else:
			print('takogo goroda net, vvedite noviy gorod pribitia')
			exit_city = input()
	
