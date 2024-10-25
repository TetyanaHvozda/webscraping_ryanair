import mysql.connector
import networkx as nx
import matplotlib.pyplot as plt

# MySQL's connection details
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="flights"
)


# Function to retrieve flight data from the database
def get_flight_data(connection):
    cursor = connection.cursor()
    query = """
    SELECT origin_airport, destination_airport
    FROM flights
    """
    cursor.execute(query)
    flight_data = cursor.fetchall()
    cursor.close()
    return flight_data


# Function to create a weighted graph and calculate Weighted Degree Centrality
def calculate_most_popular_route(flight_data):
    # Create a directed graph
    G = nx.DiGraph()

    # Add edges to the graph with weights based on the number of flights on each route
    for origin, destination in flight_data:
        if G.has_edge(origin, destination):
            G[origin][destination]['weight'] += 1  # Increase weight if route already exists
        else:
            G.add_edge(origin, destination, weight=1)  # Initialize weight if new route

    # Find the route with the highest weight
    most_popular_route = max(G.edges(data=True), key=lambda x: x[2]['weight'])
    origin, destination, data = most_popular_route
    route_weight = data['weight']

    return (origin, destination), route_weight, G


def visualize_routes(graph):
    pos = nx.spring_layout(graph)  # Layout for visualization
    weights = nx.get_edge_attributes(graph, 'weight')

    # Draw the nodes
    nx.draw_networkx_nodes(graph, pos, node_size=500, node_color="skyblue")

    # Draw edges with thickness based on weight
    nx.draw_networkx_edges(
        graph, pos, edgelist=weights.keys(), width=[w for w in weights.values()],
        edge_color='blue', arrows=True, arrowstyle='-|>'
    )

    # Draw labels for nodes
    nx.draw_networkx_labels(graph, pos, font_size=10, font_family="sans-serif")

    plt.title("Flight Routes Visualization")
    plt.show()


# Retrieve data from database
flight_data = get_flight_data(connection)

# Calculate the most popular route
most_popular_route, route_weight, G = calculate_most_popular_route(flight_data)

print(f"The most popular route is from {most_popular_route[0]} to {most_popular_route[1]} with {route_weight} flights.")

# Visualize the graph
visualize_routes(G)

# Close the MySQL connection
connection.close()
