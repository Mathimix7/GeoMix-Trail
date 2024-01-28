import csv
import io
from geopy.distance import distance
import smopy
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image
from tqdm import tqdm

class DFTrack:
    def __init__(self, directory: str, color='red', point_distance_meters=100):
        if not directory.endswith(".csv"):
            raise ValueError(f"'{directory}' is not a CSV file.")
        with open(directory, 'r') as f:
            reader = csv.DictReader(f)
            self.rows = list(reader)
        self.point_distance_meters = point_distance_meters
        self.latitudes = [float(row['Latitude']) for row in self.rows]
        self.longitudes = [float(row['Longitude']) for row in self.rows]
        self.dates = [str(row['Date']) for row in self.rows]
        self.points = {}
        for row in self.rows:
            codeRoute = row['Coderoute']
            longitude = row['Longitude']
            latitude = row['Latitude']
            if codeRoute not in self.points.keys():
                self.points[codeRoute] = []
                draw_point = True
            else:
                draw_point = distance(last, (float(latitude), float(longitude))).m >= self.point_distance_meters
            if draw_point:
                self.points[codeRoute].append((float(latitude), float(longitude)))
                last = (float(latitude), float(longitude))
        self.color = color

    def set_color(self, color):
        self.color = color

    def set_colors(self, category, colors=['red', 'orange', 'gold', 'yellow', 'limegreen', 'lime']): 
        categoryList = {}
        self.color = {}
        for row in self.rows:
            codeRoute = row['Coderoute']
            longitude = row['Longitude']
            latitude = row['Latitude']
            categoryItem = row[category]
            if codeRoute not in categoryList.keys():
                categoryList[codeRoute] = []
                draw_point = True
            else:
                draw_point = distance(last, (float(latitude), float(longitude))).m >= self.point_distance_meters
            if draw_point:
                categoryList[codeRoute].append(float(categoryItem))
                last = (float(latitude), float(longitude))
        for key, values in categoryList.items():
            min_category = min(values)
            max_category = max(values)
            norm_category = [(x - min_category) / (max_category - min_category) for x in values]
            cmap = mcolors.ListedColormap(colors)
            self.color[key] = [cmap(norm) for norm in norm_category]

class AnimationTrack:
    def __init__(self, DFTrack: DFTrack, width:int=1200, height:int=800, bg_map:bool=True, map_transparency:float=0.7):
        self.DFTrack = DFTrack
        self.width = width
        self.height = height
        self.bg_map = bg_map
        self.map_transparency = map_transparency

    def create_map(self):
        bbox = (min(self.DFTrack.latitudes), min(self.DFTrack.longitudes), max(self.DFTrack.latitudes), max(self.DFTrack.longitudes))
        map = smopy.Map(bbox)
        # map.resize(self.width, self.height)
        return map
    
    def make_image(self, output_file="image.png", linewidth=4):
        fig, ax = plt.subplots(figsize=(self.width*2/100, self.height*2/100), dpi=100)
        ax.axis('off')
        map = self.create_map()
        ax.imshow(map.img, alpha=self.map_transparency)
        for key, values in self.DFTrack.points.items():
            for i in range(len(values)-1):
                x1, y1 = map.to_pixels(self.DFTrack.points[key][i])
                x2, y2 = map.to_pixels(self.DFTrack.points[key][i+1])
                if isinstance(self.DFTrack.color, dict):
                    color = self.DFTrack.color[key][i] 
                else:
                    color = self.DFTrack.color
                ax.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth)
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
        buffer.seek(0)
        img = Image.open(buffer)
        img_resized = img.resize((self.width, self.height))
        img_resized.save(output_file)
    
    def make_video(self, output_file="video.mp4", linewidth=2, fps=30, duration=None):
        fig, ax = plt.subplots(figsize=(self.width/100, self.height/100), dpi=100)
        ax.axis('off')
        fig.tight_layout(pad=0)
        map = self.create_map()
        ax.imshow(map.img, alpha=self.map_transparency)
        points = []
        keyChanges = []
        for (key, value) in self.DFTrack.points.items():
            points.extend(value)
            keyChanges.append(len(value))
        pbar = tqdm(total=len(points))
        if duration:
            fps = len(points) / duration
        def animate(i):
            currentChange = 0
            for x, change in enumerate(keyChanges):
                currentChange += change
                if i < currentChange:
                    i = i-currentChange+change
                    break
            key = list(self.DFTrack.points.keys())[x]
            try:
                x1, y1 = map.to_pixels(self.DFTrack.points[key][i][0], self.DFTrack.points[key][i][1])
                x2, y2 = map.to_pixels(self.DFTrack.points[key][i+1][0], self.DFTrack.points[key][i+1][1])
            except:
                x2, y2 = map.to_pixels(self.DFTrack.points[key][i][0], self.DFTrack.points[key][i][1])
            x = [x1, x2]
            y = [y1, y2]
            pbar.update(1)
            if isinstance(self.DFTrack.color, dict):
                color = self.DFTrack.color[key][i] 
            else:
                color = self.DFTrack.color
            return ax.plot(x, y, color=color, linewidth=linewidth)
        anim = animation.FuncAnimation(fig, animate, frames=len(points), interval=0, blit=True)
        anim.save(output_file, fps=fps, extra_args=['-vcodec', 'libx264'])
