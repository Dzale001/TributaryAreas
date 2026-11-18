import ezdxf
import math
import json
import pandas as pd

doc = ezdxf.readfile("Disegno1.dxf")
msp = doc.modelspace()

data = {}
polylines = {}
mtexts = {}

# Questa parte definisce i lati e l'area
def polygon_sides(points):
    n = len(points)
    sides = []
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]  # richiude l'ultimo lato col primo punto
        length = math.dist(p1, p2)
        sides.append({"start": p1, "end": p2, "length": length})
    return sides

def polygon_area(points):
    n = len(points)
    area = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0

def point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

# Questa parte crea trova gli oggetti
for entity in msp:
    if entity.dxftype() == "LWPOLYLINE":
        polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed
        }
    elif entity.dxftype() == "MTEXT":
        mtexts[entity.dxf.handle] = {
            "text": entity.plain_text(),
            "insert": (float(entity.dxf.insert[0]), float(entity.dxf.insert[1]))
        }


##########################################################################################################################################################################################
# Questa parte crea i dati da inserire in data
for text_handle, tdata in mtexts.items():
    point = tdata["insert"]
    containing = []
    for poly_handle, pdata in polylines.items():
        if not pdata["closed"] or len(pdata["points"]) < 3:
            continue
        if point_in_polygon(point, pdata["points"]):
            containing.append(poly_handle)

    if not containing:
        continue  # nessun poligono trovato per questo testo, salto

    poly_points = polylines[containing[0]]["points"]

    data[tdata["text"]] = {
        "polyline_handle": containing[0],
        "all_containing": containing,
        "sides": polygon_sides(poly_points),
        "area": polygon_area(poly_points)
    }

###########################################################################################################################################################################################
# Qui creiamo il file JSON
filepath = r"C:\Users\Amministratore\Desktop\VSCode\data.JSON"
with open(filepath, "w") as f:
    json.dump(data, f, indent=2)

##########################################################################################################################################################################################
# Qui creiamo il dataframe

def get_x_y_dimensions(sides):
    dim_x = 0.0
    dim_y = 0.0
    for side in sides:
        x1, y1 = side["start"]
        x2, y2 = side["end"]
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        if dx > dy:
            dim_x = max(dim_x, side["length"])
        else:
            dim_y = max(dim_y, side["length"])
    return dim_x, dim_y

rows = []
for name, value in data.items():
    dim_x, dim_y = get_x_y_dimensions(value["sides"])
    rows.append({
        "name": name,
        "x": dim_x,
        "y": dim_y,
        "Area": value["area"]
    })

dataframe = pd.DataFrame(rows, columns=["name", "x", "y", "Area"])

# Esporto in Excel
excel_path = r"C:\Users\Amministratore\Desktop\VSCode\data.xlsx"
dataframe.to_excel(excel_path, index=False)

print(dataframe)
