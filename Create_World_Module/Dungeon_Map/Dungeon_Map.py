from yapsy.IPlugin import IPlugin
import numpy as np
import tcod.bsp
import random
import Main_Menu.Create_World_State as mapclass
import Library.UI as UI
from typing import List, Tuple, Iterator
from dataclasses import dataclass



TILE_WALL = 0
TILE_FLOOR = 1


class Dungeon_Map_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = Dungeon_Map(obj)
        return this_mod



class Dungeon_Map_Data:
    def __init__(
        self,
        position_y: int,
        position_x: int,
        height: int,
        width: int,
        max_depth: int,
        min_size: int,
        floor_config: list
    ) -> None:
        self.position_y = position_y
        self.position_x = position_x
        self.height = height
        self.width = width
        self.max_depth = max_depth
        self.min_size = min_size
        self.dungeon_map = np.zeros((height, width), dtype=np.uint8)
        # 额外数据 ── reserved 记录“已用 + 缓冲”区域
        self._buffer = 1
        self._reserved = np.zeros_like(self.dungeon_map, dtype=bool)
        self.screen: list[list[list]] = []
        self.floor_config = floor_config

    # --------------------------------------------------------
    # 房间
    def carve_room(self, node: tcod.bsp.BSP):
        """
        在叶子结点随机雕刻房间并返回中心坐标。
        若空间不足则跳过房间，但仍返回 None。
        """
        x1_min = node.x + self._buffer
        y1_min = node.y + self._buffer
        x1_max = node.x + node.width  - self.min_size - self._buffer
        y1_max = node.y + node.height - self.min_size - self._buffer
        if x1_max < x1_min or y1_max < y1_min:
            return None  # 叶子太小
        for _ in range(30):  # 最多尝试 30 次
            x1 = random.randint(x1_min, x1_max)
            y1 = random.randint(y1_min, y1_max)
            w_max = node.x + node.width  - x1 - self._buffer
            h_max = node.y + node.height - y1 - self._buffer
            w = random.randint(self.min_size, w_max)
            h = random.randint(self.min_size, h_max)
            x2, y2 = x1 + w, y1 + h  # 右下角(不含)
            # 检查区域 (含缓冲) 是否为空
            if self._reserved[y1 - self._buffer : y2 + self._buffer,
                              x1 - self._buffer : x2 + self._buffer].any():
                continue
            # 挖房
            self.dungeon_map[y1:y2, x1:x2] = 1
            self._reserved[y1 - self._buffer : y2 + self._buffer,
                           x1 - self._buffer : x2 + self._buffer] = True
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            node.room_center = (cx, cy)
            return (cx, cy)
        return None

    # --------------------------------------------------------
    # 走廊
    def carve_corridor(self, a: tuple[int, int], b: tuple[int, int]):
        """
        在两点间开通 1 格宽的 L 型走廊。优先保证 ≥1 格缓冲，
        若两条 L 形均冲突，则最后一种路线会无视缓冲强挖，
        以保证全图连通。
        """
        ax, ay = a
        bx, by = b
        def cells(order: str) -> list[tuple[int, int]]:
            if order == "h":  # 先横后竖
                hor = [(x, ay) for x in range(min(ax, bx), max(ax, bx) + 1)]
                ver = [(bx, y) for y in range(min(ay, by), max(ay, by) + 1)]
            else:            # 先竖后横
                ver = [(ax, y) for y in range(min(ay, by), max(ay, by) + 1)]
                hor = [(x, by) for x in range(min(ax, bx), max(ax, bx) + 1)]
            return hor + ver
        def ok(c_list: list[tuple[int, int]]) -> bool:
            for x, y in c_list:
                ys = slice(max(0, y - self._buffer), min(self.height, y + self._buffer + 1))
                xs = slice(max(0, x - self._buffer), min(self.width,  x + self._buffer + 1))
                if self._reserved[ys, xs].any() and (x, y) not in (a, b):
                    return False
            return True
        orders = ["h", "v"]
        random.shuffle(orders)
        for o in orders:
            c_list = cells(o)
            if ok(c_list):
                self._dig_path(c_list)
                return
        # 若均失败，强行使用第一种
        self._dig_path(cells(orders[0]), strict=False)

    def _dig_path(self, coord_list: list[tuple[int, int]], *, strict: bool = True):
        """
        将 coord_list 中的格子全部挖开，并把“格子+缓冲圈”记为 reserved。
        strict=True 表示信任该路线已与 reserved 不冲突；False 则忽略检查。
        """
        for x, y in coord_list:
            if strict:
                ys = slice(max(0, y - self._buffer), min(self.height, y + self._buffer + 1))
                xs = slice(max(0, x - self._buffer), min(self.width,  x + self._buffer + 1))
                self._reserved[ys, xs] = True
            self.dungeon_map[y, x] = 1
            self._reserved[y, x] = True

    # --------------------------------------------------------
    # 生成过程
    def generate(self):
        root = tcod.bsp.BSP(0, 0, self.width, self.height)
        root.split_recursive(
            self.max_depth,
            self.min_size + 2 * self._buffer,
            self.min_size + 2 * self._buffer,
            1.5,
            1.5,
        )
        # 1. 叶子 -> 房间
        for node in root.pre_order():
            if not node.children:
                self.carve_room(node)
        # 2. 倒序连接左右子节点中心（保证全部连通）
        for node in root.inverted_level_order():
            if len(node.children) != 2:
                continue
            left, right = node.children
            if hasattr(left, "room_center") and hasattr(right, "room_center"):
                self.carve_corridor(left.room_center, right.room_center)
                node.room_center = random.choice((left.room_center, right.room_center))

    # --------------------------------------------------------
    # 入口
    def add_entrance(self) -> tuple[int, int]:
        """
        在地图边缘挖一条狭窄通道连到最近地板，返回入口坐标。
        不需要缓冲检查，直接贯通外部世界。
        """
        edges = [
            ("top",    (lambda: (random.randint(1, self.width - 2), 0),              (0, 1))),
            ("bottom", (lambda: (random.randint(1, self.width - 2), self.height - 1),(0, -1))),
            ("left",   (lambda: (0,              random.randint(1, self.height - 2)),(1, 0))),
            ("right",  (lambda: (self.width - 1, random.randint(1, self.height - 2)),(-1, 0))),
        ]
        random.shuffle(edges)
        for _name, (pos_fn, step) in edges:
            ex, ey = pos_fn()
            dx, dy = step
            x, y = ex, ey
            while 0 <= x < self.width and 0 <= y < self.height:
                self.dungeon_map[y, x] = 1
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.dungeon_map[ny, nx] == 1:
                    return (ex, ey)
                x, y = nx, ny
        return (0, 0)  # 理论上不会运行到这里

    # --------------------------------------------------------
    # 对外接口
    def get_dungeon_map(self):
        """
        生成整图，构造 screen 结构并返回
        [MapData, numpy_map, 入口坐标]
        """
        self.generate()
        entrance = self.add_entrance()
        self.screen.clear()
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if self.dungeon_map[y, x] == 1:
                    row.append([' ', [180, 180, 180], [60, 60, 60]])
                else:
                    row.append(['▓', [180, 180, 180], [120, 120, 120]])
            self.screen.append(row)

        pass_enter = [[entrance[1], entrance[0]]]
        submap = mapclass.MapData(self.height, self.width, enter_point=list(pass_enter), walkable=list(self.dungeon_map), exit_point=list(pass_enter))
        submap.set_default_screen(self.screen)
        return submap


class Dungeon_Map:
    def __init__(self, obj) -> None:
        self.id = obj["id"]
        self.number_of_dungeon = obj["number_of_dungeon"]
        self.dmap_width = obj["dmap_width"]
        self.dmap_height = obj["dmap_height"]
        self.max_depth = obj["max_depth"]
        self.min_size = obj["min_size"]
        self.icon = obj["icon"]
        self.icon_color = obj["icon_color"]
        self.biome_exception = obj["biome_exception"]

        self.initiate_dungeon_map = False
        self.dungeon_maps = []

        self.player_id = obj["player_id"]
        self.list_submap = []
        self.start_view_dist = obj["start_view_dist"]

        self.road_char = obj["road_char"],
        self.road_fg = obj["road_fg"],
        self.road_bg = obj["road_bg"],
        self.wall_char = obj["wall_char"],
        self.wall_fg = obj["wall_fg"],
        self.wall_bg = obj["wall_bg"],
        self.floor_config = [self.road_char, self.road_fg, self.road_bg, self.wall_char, self.wall_fg, self.wall_bg]
        return

    def update(self, **kwargs) -> None:
        if not self.initiate_dungeon_map:
            maps = kwargs["map"]
            generated = 0
            while generated < self.number_of_dungeon:
                n = random.randint(0, maps.get_height() - 1)
                m = random.randint(0, maps.get_width() - 1)
                if maps.get_attribute_at("biomes", n, m) != self.biome_exception:
                    dungeon_map_data = Dungeon_Map_Data(n, m, self.dmap_height, self.dmap_width, self.max_depth, self.min_size, self.floor_config)
                    self.dungeon_maps.append(dungeon_map_data)
                    submap = dungeon_map_data.get_dungeon_map()
                    submap._view_dist = self.start_view_dist
                    self.list_submap.append(submap)
                    maps.set_submap(n, m, "dungeon entrance", self.id, submap)
                    UI.ntcod_entity(self.icon, self.icon_color, n, m, kwargs["window"].get(0)[0], self.id)
                    generated += 1
            self.initiate_dungeon_map = True

        # if self.player_id in list(kwargs["mods"].keys()):
            # player = kwargs["mods"][self.player_id]
            # if player.get_current_map() in self.list_submap

        return

    def print(self, **kwargs): # None or {"title": "level1_name", 0: {"title": "level2_name", 0: [content, spaceTF, middleTF]}}
        return

    def get_actions(self, **kwargs): # None or {"title": "level1_name", 0: {"title": "level2_name", 0: action}}
        return

    def act_on_action(self, **kwargs) -> list: # [action_time, menu_TF]
        return []
