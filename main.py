import sys
import heapq
import curses
from time import time_ns
from resource import getrusage, RUSAGE_SELF

OPTIONS_NUM = 6

MINCOST_MINTIME_MODE = 0
MINCOST_MODE = 1
MINSTATIONSNUM_MODE = 2
LIMITCOST_MODE = 3
LIMITTIME_MODE = 4
WANT_TO_EXIT = 5

city_id = {} # ключ = город, значение = id
id_city = {} # ключ = id, значение = город
trans_id = {} # ключ = тип транспорта, значение = id
id_trans = {} # ключ = id, значение = тип транспорта
trans_type = [] #список всех типов транспорта


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
	
def read_graph_from_file(file_path): #читаем данные из файла
    graph = Graph()
    with open(file_path, "r") as f:
        city_number = 0
        trans_number = 0
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): #пропускаем пустые или те, которые начинаются на #
                continue
            parts = line.split() #делим строку на части
            if len(parts) != 5:
                continue
            from_city, to_city, transport_type = parts[0].replace('"',''), parts[1].replace('"',''), parts[2].replace('"','')
            cruise_time, cruise_fare = int(parts[3]), int(parts[4])
            graph.add_edge(from_city, to_city, transport_type, cruise_time, cruise_fare)
            if (transport_type not in trans_id): #добавляем тип транспорта, если его нет в словаре
                trans_id[transport_type] = trans_number
                id_trans[trans_number] = transport_type
                trans_type.append(transport_type)
                trans_number += 1

            if (from_city not in city_id): #добавляем город, если его нет в словаре
                city_id[from_city] = city_number
                id_city[city_number] = from_city
                city_number += 1

            if (to_city not in city_id): 
                city_id[to_city] = city_number
                id_city[city_number] = to_city
                city_number += 1
    return graph


#Среди кратчайших по времени путей между двумя городами найти путь минимальной стоимости. Если город достижим из города отправления. 
def algo1(graph, start_city, exit_city, allowed_transport_types): 
    distances = {city_id[start_city]: (0, 0)} #время и стоимость
    previous_cities = {}

    for i in range(len(city_id)):
        if i != city_id[start_city]:
            distances[i] = (float("inf"), float("inf")) #расстояние до начального города 0, до всех остальных беконечность

    pq = [(0, city_id[start_city])] #приоритетная очередь

    while len(pq) > 0:
        (time, current_city) = heapq.heappop(pq)
        if current_city == city_id[exit_city]: #если достигли город прибытия, то возвращаем путь и стоимость перемещения
            path = []
            while current_city in previous_cities:
                path.append(id_city[current_city])
                current_city = previous_cities[current_city]
            path.append(id_city[city_id[start_city]])
            path.reverse()
            return (path, distances[city_id[exit_city]][1])
        for (neighbor, transport_type) in graph.edges[id_city[current_city]]: #перебор соседних городов
            if transport_type not in allowed_transport_types: #если вид транспорта не разрешен, то пропускаем
                continue
            neighbor_id = city_id[neighbor]
            trans_type_id = trans_id[transport_type]
            edge_time, edge_cost = graph.get_edge(id_city[current_city], neighbor, transport_type)
            total_time, total_cost = time + edge_time, distances[current_city][1] + edge_cost #время и стоимость до соседнего города
            if total_time < distances[neighbor_id][0]:
                distances[neighbor_id] = (total_time, total_cost)
                previous_cities[neighbor_id] = current_city
                heapq.heappush(pq, (total_time, neighbor_id))
            elif total_time == distances[neighbor_id][0] and total_cost < distances[neighbor_id][1]:
                distances[neighbor_id] = (total_time, total_cost)
                previous_cities[neighbor_id] = current_city

    return None 


#Среди путей между двумя городами найти путь минимальной стоимости. Если город достижим из города отправления. 
def algo2(graph, start_city, exit_city, allowed_transport_types):
    distances = {city_id[start_city]: 0}
    previous_cities = {}

    for i in range(len(city_id)):
        if i != city_id[start_city]:
            distances[i] = float("inf")

    pq = [(0, city_id[start_city])]

    while len(pq) > 0:
        (cost, current_city) = heapq.heappop(pq)
        if current_city == city_id[exit_city]:
            path = []
            while current_city in previous_cities:
                path.append(id_city[current_city])
                current_city = previous_cities[current_city]
            path.append(id_city[city_id[start_city]])
            path.reverse()
            return (path, cost)
        for (neighbor, transport_type) in graph.edges[id_city[current_city]]:
            if transport_type not in allowed_transport_types:
                continue
            neighbor_id = city_id[neighbor]
            trans_type_id = trans_id[transport_type]
            edge_cost = graph.get_edge(id_city[current_city], neighbor, transport_type)[1]
            total_cost = cost + edge_cost
            if total_cost < distances[neighbor_id]: #если новое расстояние до соседа меньше текущего, то обновляем его
                distances[neighbor_id] = total_cost
                previous_cities[neighbor_id] = current_city
                heapq.heappush(pq, (total_cost, neighbor_id))

    return None

	
#Найти путь между 2-мя городами минимальный по числу посещенных городов. 
def algo3(graph, start_city, exit_city, allowed_transport_types):
    start_id = city_id[start_city]#отправной путь
    exit_id = city_id[exit_city]#конечный путь
    visited = set([start_id])#множество посещенных городов
    queue = [(start_id, [start_id])]

    while queue:
        current_id, path = queue.pop(0)

        if current_id == exit_id:
            return [id_city[city_id] for city_id in path]

        for neighbor, transport_type in graph.edges[id_city[current_id]]: #обходим всех соседей текущего города и добавляем их в очередь, если они не были еще посещены
            if transport_type not in allowed_transport_types:
                continue
            neighbor_id = city_id[neighbor]

            if neighbor_id not in visited: #если сосед не был посещен, добавляем соседа в множество посещенных городов
                visited.add(neighbor_id)
                queue.append((neighbor_id, path + [neighbor_id]))#добавляем соседа в очередь поиска

    return None


#Найти множество городов, достижимых из города отправления не более чем за limit_cost денег и вывести кратчайшие по деньгам пути к ним. 	
def algo4(graph, start_city, limit_cost, allowed_transport_types): 
    visited_cities = set()
    previous_cities = {}
    reachable_cities = {}

    pq = [(0, city_id[start_city])]

    while pq:
        (cost, current_city) = heapq.heappop(pq)
        if cost > limit_cost: #если стоимость маршруты превышает предел, завершаем поиск
            break
        if current_city in visited_cities:
            continue
        visited_cities.add(current_city)
        for (neighbor, transport_type) in graph.edges[id_city[current_city]]:#перебор соседних городов и нахождение стоимости до них
            if transport_type not in allowed_transport_types:
                continue
            neighbor_id = city_id[neighbor]
            trans_type_id = trans_id[transport_type]
            edge_cost = graph.get_edge(id_city[current_city], neighbor, transport_type)[1]
            total_cost = cost + edge_cost
            if total_cost <= limit_cost: #если стоимость не превышает лимит, то добавляем город в очередь
                previous_cities[neighbor_id] = current_city
                heapq.heappush(pq, (total_cost, neighbor_id))
                if total_cost not in reachable_cities: #добавляение города в словарь достижимых городов
                    reachable_cities[total_cost] = []
                reachable_cities[total_cost].append(id_city[neighbor_id])
    result = {}
    for cost in reachable_cities: #перебор достижимых городов и создание кратчайшего маршрута до них
        for city in reachable_cities[cost]:
            path = []
            current_city = city_id[city]
            while current_city in previous_cities:
                path.append(id_city[current_city])
                current_city = previous_cities[current_city]
            path.append(start_city)
            path.reverse()
            result[city] = (path, cost) #добавляем маршрут в результат


    return result


#Найти множество городов достижимое из города отправителя не более чем за limit_time времени и вывести кратчайшие пути по времени к ним.	
def algo5(graph, start_city, limit_time, allowed_transport_types):
    visited_cities = set()
    previous_cities = {}
    reachable_cities = {}

    pq = [(0, city_id[start_city])]

    while pq:
        (time, current_city) = heapq.heappop(pq)
        if time > limit_time: #если время маршрута превышает предел, завершаем поиск
            break
        if current_city in visited_cities:
            continue
        visited_cities.add(current_city)
        for (neighbor, transport_type) in graph.edges[id_city[current_city]]: #перебор соседних городов и нахождение времени до них
            if transport_type not in allowed_transport_types:
                continue
            neighbor_id = city_id[neighbor]
            trans_type_id = trans_id[transport_type]
            edge_time = graph.get_edge(id_city[current_city], neighbor, transport_type)[0]
            total_time = time + edge_time
            if total_time <= limit_time: #если время не превышает лимит, то добавляем город в очередь
                previous_cities[neighbor_id] = current_city
                heapq.heappush(pq, (total_time, neighbor_id))
                if total_time not in reachable_cities: #добавляение города в словарь достижимых городов
                    reachable_cities[total_time] = []
                reachable_cities[total_time].append(id_city[neighbor_id])

    result = {}
    for time in reachable_cities:
        for city in reachable_cities[time]:
            path = []
            current_city = city_id[city]
            while current_city in previous_cities:
                path.append(id_city[current_city])
                current_city = previous_cities[current_city]
            path.append(start_city)
            path.reverse()
            result[city] = (path, time)

    return result


def main(stdscr):
    file_path = sys.argv[1]
    graph = read_graph_from_file(file_path)

    want_to_exit = False

    stdscr.scrollok(True)
    stdscr.keypad(True)

    while not want_to_exit:

        current_item_index = 0
        choice_made = False

        curses.noecho()

        choices = ["Нахождение пути минимальной стоимости среди кратчайших путей между двумя городами",
           "Нахождение пути минимальной стоимости между двумя городами",
           "Нахождение пути между двумя городами с минимальным числом пересадок",
           "Нахождение городов, достижимых из города отправления не более чем за лимит стоимости, и путей к ним",
           "Нахождение городов, достижимых из города отправления не более чем за лимит времени, и путей к ним",
           "Выйти из программы"]

        while not choice_made:
            stdscr.clear()
            curses.curs_set(0)
            stdscr.addstr("Выберите желаемый режим работы программы:\n\n")
            stdscr.refresh()

            for i in range(OPTIONS_NUM):
                if i == current_item_index:
                    stdscr.attron(curses.A_STANDOUT)
                    stdscr.addstr(f"{choices[i]}\n")
                    stdscr.attroff(curses.A_STANDOUT)
                else:
                    stdscr.addstr(f"{choices[i]}\n")
                stdscr.refresh()

            key = stdscr.getch() #ожидаем ввод пользователя
            if key == curses.KEY_UP:
                if current_item_index > 0:
                    current_item_index -= 1
                else:
                    current_item_index = OPTIONS_NUM - 1
            elif key == curses.KEY_DOWN:
                if current_item_index < OPTIONS_NUM - 1:
                    current_item_index += 1
                else:
                    current_item_index = 0
            elif key == curses.KEY_ENTER or key == 10 or key == 13: #обработка ввода пользователя
                choice_made = True

        if current_item_index >= 0 and current_item_index <= OPTIONS_NUM - 2: #если выбран режим работы от 0 до последнего, то у пользователя запрашиваем разрешенные виды транспорта
            flag_0 = False
            was_transport_error = False
            while flag_0 == False:
                stdscr.clear()
                if was_transport_error:
                    stdscr.addstr(f"Транспорта вида {transport_type} нет, повторите ввод\n")
                was_transport_error = False
                stdscr.addstr("Введите разрешенные виды транспорта (через пробел). Если хотите разрешить все виды транспорта, то просто нажмите ENTER:\n\n")
                stdscr.refresh()
                curses.curs_set(1)
                curses.echo()

                allowed_transport_types_str = str(stdscr.getstr(), "utf-8", errors="ignore") #считываем строку и разбиваем ее на разрешенные виды транспорта                   
                allowed_transport_types = allowed_transport_types_str.split(" ")
                if allowed_transport_types == [""]:
                    allowed_transport_types = trans_type
                    flag_0 = True
                else:
                    for transport_type in allowed_transport_types: #проверяем, что каждый вид транспорта существует
                        if transport_type not in trans_type:
                            was_transport_error = True
                            break
                    if not was_transport_error: #если введено неверно, то запрашиваем разрешенные виды транспорта еще раз
                        flag_0 = True

        curses.echo()

        if current_item_index == MINCOST_MINTIME_MODE: #если выбран первый алгоритм
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error: #если ошибка при вводе города отправителя, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город отправителя                
                if start_city not in city_id: #проверяем есть ли такой город
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            flag_2 = False
            was_exit_city_error = False
            while flag_2 == False:
                stdscr.clear()
                if was_exit_city_error: #если ошибка при вводе города прибытия, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город прибытия\n")
                stdscr.addstr("Введите город прибытия:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                exit_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город прибытия                    
                if exit_city not in city_id: #проверяем есть ли такой город
                    was_exit_city_error = True
                else:
                    flag_2 = True
                    was_exit_city_error = False

            #Запуск первого алгоритма
            result = algo1(graph, start_city, exit_city, allowed_transport_types)

            stdscr.clear() #очищаем экран и выводим результат первого алгоритма
            if result is None:
                stdscr.addstr("Нет пути между выбранными городами c использованием указанных доступных видов транспорта\n")
            else:
                stdscr.addstr(f"Путь минимальной стоимости среди кратчайших по времени путей, используя доступные виды транспорта: {result[0]}\n")
                stdscr.addstr(f"Минимальная стоимость: {result[1]}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()
                
        elif current_item_index == MINCOST_MODE: #если выбран второй алгоритм
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error: #если ошибка при вводе города отправителя, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город отправителя                      
                if start_city not in city_id: #проверяем есть ли такой город
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            flag_2 = False
            was_exit_city_error = False
            while flag_2 == False:
                stdscr.clear()
                if was_exit_city_error: #если ошибка при вводе города прибытия, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город прибытия\n")
                stdscr.addstr("Введите город прибытия:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                exit_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город прибытия                       
                if exit_city not in city_id: #проверяем есть ли такой город
                    was_exit_city_error = True
                else:
                    flag_2 = True
                    was_exit_city_error = False

            #Запуск второго алгоритма
            result = algo2(graph, start_city, exit_city, allowed_transport_types)

            stdscr.clear() #очищаем экран и выводим результат второго алгоритма
            if result is None:
                stdscr.addstr("Нет пути между выбранными городами c использованием указанных доступных видов транспорта\n")
            else:
                stdscr.addstr(f"Путь минимальной стоимости, используя доступные виды транспорта: {result[0]}\n")
                stdscr.addstr(f"Минимальная стоимость: {result[1]}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()

        elif current_item_index == MINSTATIONSNUM_MODE: #если выбран третий алгоритм
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error: #если ошибка при вводе города отправления, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город отправления                      
                if start_city not in city_id: #проверяем есть ли такой город
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            flag_2 = False
            was_exit_city_error = False
            while flag_2 == False:
                stdscr.clear()
                if was_exit_city_error: #если ошибка при вводе города прибытия, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город прибытия\n")
                stdscr.addstr("Введите город прибытия:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                exit_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город прибытия                          
                if exit_city not in city_id: #проверяем есть ли такой город
                    was_exit_city_error = True
                else:
                    flag_2 = True
                    was_exit_city_error = False

            #Запуск третьего алгоритма
            result = algo3(graph, start_city, exit_city, allowed_transport_types)

            stdscr.clear() #очищаем экран и выводим результат третьего алгоритма
            if result is None:
                stdscr.addstr("Нет пути между выбранными городами c использованием указанных доступных видов транспорта\n")
            else:
                stdscr.addstr(f"Минимальный по числу посещенных городов путь, используя доступные виды транспорта: {result}\n")
                stdscr.addstr(f"Количество посещенных городов: {len(result) - 1}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()

        elif current_item_index == LIMITCOST_MODE: #если выбран четвертый алгоритм
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error: #если ошибка при вводе города отправления, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город отправления                        
                if start_city not in city_id: #проверяем есть ли такой город
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False
                            
            #Запуск четвертого алгоритма  
            stdscr.clear()
            stdscr.addstr("Введите лимит стоимости:\n") #запрашиваем лимит стоимости
            stdscr.refresh()
            curses.curs_set(1)
            
            while True: #ввод лимита стоимости и обработка возможных ошибок
            	try:
            		limit_cost = int(str(stdscr.getstr(), "utf-8", errors="ignore"))
            		if limit_cost < 0:
            			stdscr.clear()
            			stdscr.addstr("Лимит стоимости не может быть отрицательным. Попробуйте еще раз:\n")
            			stdscr.refresh()
            			continue
            		break
            	except ValueError:
            		stdscr.clear()
            		stdscr.addstr("Некорректный ввод. Лимит стоимости должен быть целым числом. Попробуйте еще раз:\n")
            		stdscr.refresh()
            		continue
            		
            reachable_cities = algo4(graph, start_city, limit_cost, allowed_transport_types)                     

            stdscr.clear() #очищаем экран и выводим результат четвертого алгоритма
            if not reachable_cities:
                stdscr.addstr(f"Нет городов, достижимых из {start_city} за {limit_cost} рублей, c использованием указанных доступных видов транспорта\n")
            else:
                stdscr.addstr(f"Города, достижимые из {start_city} за {limit_cost} рублей:\n")
                for city in reachable_cities:
                    stdscr.addstr(f"{city}: {reachable_cities[city][0]} (стоимость: {reachable_cities[city][1]})\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()
                        
        elif current_item_index == LIMITTIME_MODE: #если выбран пятый алгоритм
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error: #если ошибка при вводе города отправления, то запрашиваем его еще раз
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore") #получаем введенный город отправления                        
                if start_city not in city_id: #проверяем есть ли такой город
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            #Запуск пятого алгоритма		
            stdscr.clear()
            stdscr.addstr("Введите лимит времени:\n") #запрашиваем лимит времени
            stdscr.refresh()
            curses.curs_set(1)
            
            while True: #ввод лимита времени и обработка возможных ошибок
            	try:
            		limit_time = int(str(stdscr.getstr(), "utf-8", errors="ignore"))
            		if limit_time < 0:
            			stdscr.clear()
            			stdscr.addstr("Лимит времени не может быть отрицательным. Попробуйте еще раз:\n")
            			stdscr.refresh()
            			continue
            		break
            	except ValueError:
            		stdscr.clear()
            		stdscr.addstr("Некорректный ввод. Лимит времени должен быть целым числом. Попробуйте еще раз:\n")
            		stdscr.refresh()
            		continue

            reachable_cities = algo5(graph, start_city, limit_time, allowed_transport_types)

            stdscr.clear() #очищаем экран и выводим результат пятого алгоритма
            if not reachable_cities:
                stdscr.addstr(f"Нет городов, достижимых из {start_city} за {limit_cost} единицу времени, c использованием указанных доступных видов транспорта\n")
            else:
                stdscr.addstr(f"Города, достижимые из {start_city} за {limit_time} единицу времени:\n")
                for city in reachable_cities:
                    stdscr.addstr(f"{city}: {reachable_cities[city][0]} (время: {reachable_cities[city][1]})\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()
                
        elif current_item_index == WANT_TO_EXIT: #если текущий выбранный элемент = хочу_выйти
            want_to_exit = True                

        curses.endwin() # завершаем работу


if __name__ == "__main__":
    curses.wrapper(main)
