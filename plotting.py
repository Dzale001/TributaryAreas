import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon as MplPolygon
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
fig, ax = plt.subplots(figsize = (12, 10))
colors = {
    "bound": "blue",
    "struct": "red",
    "text" :"green",
    "voronoi":"black"
}

def _iter_polygons(geom):
    if isinstance(geom, Polygon):
        yield geom
    elif isinstance(geom, MultiPolygon):
        yield from geom.geoms
    # altri tipi (GeometryCollection, None, geometrie vuote) vengono ignorati

def init_plot():
    plt.ion()
    fig, ax = plt.subplots(figsize = (12, 10))
    ax.set_aspect("equal")
    return fig, ax

def update_plot(ax, geometries, pause=1):
    ax.clear()
    ax.set_aspect("equal")
    for geom in geometries:
        if geom is None or geom.is_empty:
            continue
        for poly in _iter_polygons(geom):
            x, y = poly.exterior.xy
            ax.fill(x, y, alpha=0.5, edgecolor="black")
    plt.draw()
    plt.pause(pause)

def show():
    plt.ioff()
    plt.show()

def plotting(bound_polylines, struct_polylines, mtexts, voronoi):
    for handle, data in bound_polylines.items():
        points = np.array(data["points"])
        polygon = MplPolygon(points, 
                            closed=data["closed"], 
                            fill=False, 
                            edgecolor=colors['bound'], 
                            linewidth=2,
                            label='Contorno' if handle == list(bound_polylines.keys())[0] else "")
        
        ax.add_patch(polygon)
        ax.plot(points[:, 0], points[:, 1], 'o', color=colors['bound'], markersize=4)

    for handle, data in struct_polylines.items():
        points = np.array(data["points"])
        polygon = MplPolygon(points, 
                            closed=data["closed"], 
                            fill=False, 
                            edgecolor=colors['struct'], 
                            linewidth=2,
                            label='Strutturale' if handle == list(struct_polylines.keys())[0] else "")
        
        ax.add_patch(polygon)
        polygon_filled = MplPolygon(points, 
                                    closed=data["closed"], 
                                    fill=True, 
                                    facecolor=colors['struct'], 
                                    alpha=0.15)
        ax.add_patch(polygon_filled)
        ax.plot(points[:, 0], points[:, 1], 's', color=colors['struct'], markersize=4)
    for handle, data in mtexts.items():
        x, y = data["insert"]
        
        ax.plot(x, y, '^', color=colors['text'], markersize=8, 
                label='Testo' if handle == list(mtexts.keys())[0] else "")
        ax.text(x, y + 0.5, data["text"], 
                fontsize=8, 
                color='darkgreen',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7),
                ha='center')


    n_cells = len(voronoi)
    cmap = plt.colormaps['tab20'].resampled(n_cells) if n_cells <= 20 else plt.colormaps['gist_ncar'].resampled(n_cells)
    handle_to_color = { handle: mcolors.to_hex(cmap(i)) for i, handle in enumerate(voronoi.keys())}

    for handle, data in voronoi.items():
            #print(data)
            points = np.array(data["geometry"])
            color = handle_to_color[handle]
            polygon = MplPolygon(points, 
                                fill=True,
                                facecolor = color ,
                                edgecolor = "black", 
                                linewidth=0.5,
                                alpha=0.5,
                                label='Contorno' if handle == list(voronoi.keys())[0] else "")
            
            ax.add_patch(polygon)
            ax.plot(points[:, 0], points[:, 1], '-', color=colors['voronoi'], markersize=4)

    all_points = []
    for data in bound_polylines.values():
        all_points.extend(data["points"])
    for data in struct_polylines.values():
        all_points.extend(data["points"])
    for data in voronoi.values():
        all_points.extend(data["geometry"])

    if all_points:
        all_points = np.array(all_points)
        x_min, x_max = all_points[:, 0].min(), all_points[:, 0].max()
        y_min, y_max = all_points[:, 1].min(), all_points[:, 1].max()
        
        margin = max((x_max - x_min), (y_max - y_min)) * 0.1
        ax.set_xlim(x_min - margin, x_max + margin)
        ax.set_ylim(y_min - margin, y_max + margin)

    # Aggiungi griglia e legenda
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    ax.legend(loc='upper right')
    ax.set_title("Geometria DXF - Visualizzazione", fontsize=14, fontweight='bold')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    plt.tight_layout()
    plt.show()