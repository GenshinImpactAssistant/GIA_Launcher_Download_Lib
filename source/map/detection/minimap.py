import typing as t

import cv2
from cached_property import cached_property

from source.common import timer_module
from source.map.detection.resource import MiniMapResource
from source.map.detection.utils import *
from source.map.extractor.convert import MapConverter
from source.funclib.small_map import jwa_4, posi_map
from source.util import *
from source.interaction.interaction_core import itt
from source.common.timer_module import Timer


# ONE_CHANNEL = 1
# THREE_CHANNEL = 3

class MiniMap(MiniMapResource):

    pos_change_timer = Timer(diff_start_time=30)

    def init_position(self, position: t.Tuple[int, int]):
        # logger.info(f"init_position:{position}")
        self.position = position

        # if CV_DEBUG_MODE:
        #     cv2.imshow('search_image', itt.capture())
        #     cv2.waitKey(1)

    def _get_minimap(self, image, radius):
        area = area_offset((-radius, -radius, radius, radius), offset=self.MINIMAP_CENTER)
        image = crop(image, area)
        return image

    def get_img_near_posi(self, image, posi):
        scale = self.POSITION_SCALE_DICT['wild']
        # image = np.zeros_like((1080,1920,3), dtype="uint8")
        image = self._get_minimap(image, self.MINIMAP_POSITION_RADIUS)
        image = rgb2luma(image)
        image &= self._minimap_mask
        scale *= self.POSITION_SEARCH_SCALE
        local = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        # Product search area
        search_position = np.array(posi, dtype=np.int64)
        search_size = np.array(image_size(local)) * self.POSITION_SEARCH_RADIUS
        search_size = (search_size // 2 * 2).astype(np.int64)
        search_area = area_offset((0, 0, *search_size), offset=(-search_size // 2).astype(np.int64))
        search_area = area_offset(search_area, offset=np.multiply(search_position, self.POSITION_SEARCH_SCALE))
        search_area = np.array(search_area).astype(np.int64)
        search_image = crop(self.TChannelGIMAP, search_area)
        return search_image

    def _predict_position(self, image, scale):
        """
        Args:
            image:
            scale:

        Returns:
            float: Precise similarity
            float: local_sim
            tuple[float, float]: Location on GIMAP
        """
        scale *= self.POSITION_SEARCH_SCALE
        local = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        # Product search area
        search_position = np.array(self.position, dtype=np.int64)
        search_size = np.array(image_size(local)) * self.POSITION_SEARCH_RADIUS
        search_size = (search_size // 2 * 2).astype(np.int64)
        search_area = area_offset((0, 0, *search_size), offset=(-search_size // 2).astype(np.int64))
        search_area = area_offset(search_area, offset=np.multiply(search_position, self.POSITION_SEARCH_SCALE))
        # search_size = [212,212]
        # search_area = [search_position[0]-search_size[0]/2,search_position[1]-search_size[1]/2,search_position[0]+search_size[0]/2,search_position[1]+search_size[1]/2,]

        search_area = np.array(search_area).astype(np.int64)
        # if channel == ONE_CHANNEL:
        search_image = crop(self.GIMAP, search_area)
        if CV_DEBUG_MODE:
            # cv2.destroyWindow('search_image')
            cv2.imshow('search_image', search_image.copy())
            cv2.waitKey(1)
        # elif channel == THREE_CHANNEL:
        #     search_image = crop(self.TChannelGIMAP, search_area)

        result = cv2.matchTemplate(search_image, local, cv2.TM_CCOEFF_NORMED)
        _, sim, _, loca = cv2.minMaxLoc(result)
        # result[result <= 0] = 0
        # Image.fromarray((result * 255).astype(np.uint8)).save('match_result.png')

        # Gaussian filter to get local maximum
        local_maximum = cv2.subtract(result, cv2.GaussianBlur(result, (5, 5), 0))
        _, local_sim, _, loca = cv2.minMaxLoc(local_maximum)

        # local_maximum[local_maximum < 0] = 0
        # local_maximum[local_maximum > 0.1] = 0.1
        # Image.fromarray((local_maximum * 255 * 10).astype(np.uint8)).save('local_maximum.png')

        # Calculate the precise location using CUBIC
        precise = crop(result, area=area_offset((-4, -4, 4, 4), offset=loca))
        precise_sim, precise_loca = cubic_find_maximum(precise, precision=0.05)
        precise_loca -= 5

        # Location on search_image
        lookup_loca = precise_loca + loca + np.array(image_size(image)) * scale / 2
        # Location on GIMAP
        global_loca = (lookup_loca + search_area[:2]) / self.POSITION_SEARCH_SCALE
        # Can't figure out why but the result_of_0.5_lookup_scale + 0.5 ~= result_of_1.0_lookup_scale
        global_loca += self.POSITION_MOVE
        return precise_sim, local_sim, global_loca

    @property
    def _position_scale_dict(self) -> t.Dict[str, float]:
        """
        Map:
        outer border     inner border
             v                v
        wild |   transition   | city
             |      area      |

        Scene to predict:
        wild |   wild + city  | city
        """
        dic = {}
        if not self._position_in_GICityInner(self.position):
            dic['wild'] = self.POSITION_SCALE_DICT['wild']
        if self._position_in_GICityOuter(self.position):
            dic['city'] = self.POSITION_SCALE_DICT['city']
        return dic

    def update_position(self, origin_image):
        """
        Get position on GIMAP, costs about 1.41ms.

        The following attributes will be set:
        - position_similarity
        - position
        - position_scene
        """
        # if origin_image.shape[2]==4:
        #     image = itt.png2jpg(origin_image, channel='bg', alpha_num=252)
        # else:
        image = origin_image
        image = self._get_minimap(image, self.MINIMAP_POSITION_RADIUS)

        image_one = image.copy()
        image_one = rgb2luma(image)
        image_one &= self._minimap_mask
        if CV_DEBUG_MODE:
            cv2.imshow('image_one', image_one)
            cv2.waitKey(1)
        # image_three = image.copy()
        # image_three &= np.expand_dims(self._minimap_mask,axis=2).repeat(3,axis=2)

        best_sim = -1.
        best_local_sim = -1.
        best_loca = (0, 0)
        best_scene = 'wild'
        for scene, scale in self._position_scale_dict.items(): # : ['city','wild']
            # if scene == 'wild':
            inp_img = image_one
            # channel = ONE_CHANNEL
            # else:
            #     inp_img = image_three
            #     channel = THREE_CHANNEL
            if CV_DEBUG_MODE:
                print(scene)
            similarity, local_sim, location = self._predict_position(inp_img, scale)
            # print(scene, scale, similarity, location)
            if similarity > best_sim:
                best_sim = similarity
                best_local_sim = local_sim
                best_loca = location
                best_scene = scene
                # best_channel = channel
        if self.verify_position(tuple(np.round(best_loca, 1))):
            self.position_similarity = round(best_sim, 5)
            self.position_similarity_local = round(best_local_sim, 5)
            self.position = tuple(np.round(best_loca, 1))
            self.scene = best_scene
        # self.channel = best_channel
        # logger.trace(f'P:({float2str(self.position[0], 4)}, {float2str(self.position[1], 4)}) ')
        return self.position



    def verify_position(self, pos):
        dt = self.pos_change_timer.get_diff_time()
        if dt > 20:
            self.pos_change_timer.reset()
            return True
        else:
            if euclidean_distance(pos, self.position) >= self.MOVE_SPEED * dt + 1:
                logger.warning(f'position change above limit: {euclidean_distance(pos, self.position)} >= {self.MOVE_SPEED * dt + 1}. result will be abandon.')
                return False
            else:
                self.pos_change_timer.reset()
                return True


    def update_direction(self, image):
        """
        Get direction of character, costs about 0.64ms.

        The following attributes will be set:
        - direction_similarity
        - direction
        """
        if image.shape[2] == 4:
            image = image[:, :, :3]
        image = self._get_minimap(image, self.DIRECTION_RADIUS)

        image = color_similarity_2d(image, color=(0, 229, 255))
        try:
            area = area_pad(get_bbox(image, threshold=128), pad=-1)
        except IndexError:
            # IndexError: index 0 is out of bounds for axis 0 with size 0
            logger.warning('No direction arrow on minimap')
            return
        image = crop(image, area=area)
        scale = self.DIRECTION_ROTATION_SCALE * self.DIRECTION_SEARCH_SCALE
        mapping = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        result = cv2.matchTemplate(self.ArrowRotateMap, mapping, cv2.TM_CCOEFF_NORMED)
        result = cv2.subtract(result, cv2.GaussianBlur(result, (5, 5), 0))
        _, sim, _, loca = cv2.minMaxLoc(result)
        loca = np.array(loca) / self.DIRECTION_SEARCH_SCALE // (self.DIRECTION_RADIUS * 2)
        degree = int((loca[0] + loca[1] * 8) * 5)

        def to_map(x):
            return int((x * self.DIRECTION_RADIUS * 2 + self.DIRECTION_RADIUS) * self.POSITION_SEARCH_SCALE)

        # Row on ArrowRotateMapAll
        row = int(degree // 8) + 45
        # Calculate +-1 rows to get result with a precision of 1
        row = (row - 2, row + 3)
        # Convert to ArrowRotateMapAll and to be 5px larger
        row = (to_map(row[0]) - 5, to_map(row[1]) + 5)

        precise_map = self.ArrowRotateMapAll[row[0]:row[1], :]
        result = cv2.matchTemplate(precise_map, mapping, cv2.TM_CCOEFF_NORMED)
        result = cv2.subtract(result, cv2.GaussianBlur(result, (5, 5), 0))

        def to_map(x):
            return int((x * self.DIRECTION_RADIUS * 2) * self.POSITION_SEARCH_SCALE)

        def get_precise_sim(d):
            y, x = divmod(d, 8)
            im = result[to_map(y):to_map(y + 1), to_map(x):to_map(x + 1)]
            _, sim, _, _ = cv2.minMaxLoc(im)
            return sim

        precise = np.array([[get_precise_sim(_) for _ in range(24)]])
        precise_sim, precise_loca = cubic_find_maximum(precise, precision=0.1)
        precise_loca = degree // 8 * 8 - 8 + precise_loca[0]

        self.direction_similarity = round(precise_sim, 3)
        self.direction = precise_loca % 360
        # Convert
        if self.direction > 180:
            self.direction = 360 - self.direction
        else:
            self.direction = -self.direction
        return self.direction

    def _get_minimap_subtract(self, image, update_position=True):
        """
        Subtract the corresponding background from the current minimap
        to obtain the white translucent area of camera rotation

        Args:
            image:
            update_position (bool): False to reuse position result

        Returns:
            np.ndarray
        """
        if update_position:
            self.update_position(image)

        # Get current minimap
        scale = self.POSITION_SCALE_DICT[self.scene] * self.POSITION_SEARCH_SCALE
        minimap = self._get_minimap(image, radius=self.MINIMAP_RADIUS)
        minimap = rgb2luma(minimap)

        radius = self.MINIMAP_RADIUS * scale
        area = area_offset((-radius, -radius, radius, radius),
                           offset=np.array(self.position) * self.POSITION_SEARCH_SCALE)
        # Search 15% larger
        area = area_pad(area, pad=-int(radius * 0.15))
        area = np.array(area).astype(int)

        # Crop GIMAP around current position and resize to current minimap
        image = crop(self.GIMAP, area)
        image = cv2.resize(image, None, fx=1 / scale, fy=1 / scale, interpolation=cv2.INTER_LINEAR)
        # Search best match
        result = cv2.matchTemplate(image, minimap, cv2.TM_CCOEFF_NORMED)
        sim, loca = cubic_find_maximum(result, precision=0.05)
        # Re-crop the GIMAP that best match current map
        area = (0, 0, self.MINIMAP_RADIUS * 2, self.MINIMAP_RADIUS * 2)
        src = area2corner(area_offset(area, loca)).astype(np.float32)
        dst = area2corner(area).astype(np.float32)
        homo = cv2.getPerspectiveTransform(src, dst)
        image = cv2.warpPerspective(image, homo, area[2:], flags=cv2.INTER_LINEAR)

        # current - background
        minimap = minimap.astype(float)
        image = image.astype(float)
        image = (255 - image) / (255 - minimap + 0.1) * 128
        image = cv2.min(cv2.max(image, 0), 255)
        image = image.astype(np.uint8)
        return image

    def _predict_rotation(self, image, use_alpha=False):
        if not use_alpha:
            d = self.MINIMAP_RADIUS * 2
            # Upscale image and apply Gaussian filter for smother results
            scale = 2
            image = cv2.GaussianBlur(image, (3, 3), 0)
            # Expand circle into rectangle
            remap = cv2.remap(image, *self.RotationRemapData, cv2.INTER_LINEAR)[d * 1 // 10:d * 5 // 10].astype(
                np.float32)
            remap = cv2.resize(remap, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
            # Find derivative
            gradx = cv2.Scharr(remap, cv2.CV_32F, 1, 0)
            # plt.imshow(gradx)
            # plt.show()

            # Magic parameters for scipy.find_peaks
            para = {
                # 'height': (50, 800),
                'height': 50,
                # 'prominence': (0, 400),
                # 'width': (0, d * scale / 20),
                # 'distance': d * scale / 18,
                'wlen': d * scale,
            }
            # plt.plot(gradx[d * 3 // 10])
            # plt.show()

            # `l` for the left of sight area, derivative is positive
            # `r` for the right of sight area, derivative is negative
            l = np.bincount(signal.find_peaks(gradx.ravel(), **para)[0] % (d * scale), minlength=d * scale)
            r = np.bincount(signal.find_peaks(-gradx.ravel(), **para)[0] % (d * scale), minlength=d * scale)
            l, r = np.maximum(l - r, 0), np.maximum(r - l, 0)
            # plt.plot(l)
            # plt.plot(np.roll(r, -d * scale // 4))
            # plt.show()

            conv0 = []
            kernel = 2 * scale
            for offset in range(-kernel + 1, kernel):
                result = l * convolve(np.roll(r, -d * scale // 4 + offset), kernel=3 * scale)
                minus = l * convolve(np.roll(r, offset), kernel=10 * scale) // 5
                # if offset == 0:
                #     plt.plot(result)
                #     plt.plot(-minus)
                #     plt.show()
                result -= minus
                result = convolve(result, kernel=3 * scale)
                conv0 += [result]
            # plt.figure(figsize=(20, 16))
            # for row in conv0:
            #     plt.plot(row)
            # plt.show()

            conv0 = np.array(conv0)
            conv0[conv0 < 1] = 1
            maximum = np.max(conv0, axis=0)
            if peak_confidence(maximum) > 0.3:
                # Good match
                result = maximum
            else:
                # Convolve again to reduce noice
                average = np.mean(conv0, axis=0)
                minimum = np.min(conv0, axis=0)
                result = convolve(maximum * average * minimum, 2 * scale)
            # plt.plot(maximum)
            # plt.plot(result)
            # plt.show()

            # Convert match point to degree
            self.degree = np.argmax(result) / (d * scale) * 2 * np.pi + np.pi / 4
            degree = np.argmax(result) / (d * scale) * 360 + 135
            degree = int(degree % 360)
            self.rotation = degree

            # Calculate confidence
            self.rotation_confidence = round(peak_confidence(result), 3)

            # Convert
            if degree > 180:
                degree = 360 - degree
            else:
                degree = -degree
            self.rotation = degree

            # Calculate confidence
            self.rotation_confidence = round(peak_confidence(result), 3)
            return degree
        else:
            self.rotation_confidence = 0.9
            degree = jwa_4(itt.capture(posi=posi_map, jpgmode=FOUR_CHANNELS))
            self.rotation = degree
            self.degree = degree
            return degree

    @timer_module.timer
    def update_rotation(self, image, layer=MapConverter.LAYER_Teyvat, update_position=True):
        pt = time.time()
        # if image.shape[2]==4:
        #     image = image[:,:,:3]
        #     use_alpha = (self.scene == 'city')
        # else:
        #     use_alpha = False
        use_alpha = False
        # minimap = self._get_minimap(image, radius=self.MINIMAP_RADIUS)
        # minimap = rgb2luma(minimap)
        if (not use_alpha) or (self.scene != 'city'):
            if layer == MapConverter.LAYER_Domain:
                minimap = self._get_minimap(image, radius=self.MINIMAP_RADIUS)
                minimap = rgb2luma(minimap)
            else:
                minimap = self._get_minimap_subtract(image, update_position=update_position)
            self.rotation = self._predict_rotation(minimap, use_alpha=False)
            if CV_DEBUG_MODE:
                self.show_rotation(minimap, self.degree)
            # if THE_COMPUTER_IS_TOO_GOOD:
            #     if time.time() - pt < 0.025:
            #         time.sleep(0.025)
                    # self.show_rotation(minimap, self.degree)
        else:
            minimap = None
            self.rotation = self._predict_rotation(minimap, use_alpha=True)

        return self.rotation

    @cached_property
    def _named_window(self):
        return cv2.namedWindow('result')

    def show_rotation(self, img, ang):
        _ = self._named_window
        if ang is not None:
            img = cv2.line(img, (img.shape[0] // 2, img.shape[0] // 2),
                           (int(img.shape[0] // 2 + 1000 * np.cos(ang)), int(img.shape[0] // 2 + 1000 * np.sin(ang))),
                           (255, 255, 0), 2)
        cv2.imshow('result', img)
        cv2.waitKey(1)

    def update_minimap(self, image):
        """
        Args:
            image:
        """
        self.update_position(image)
        self.update_direction(image)
        self.update_rotation(image, layer=MapConverter.LAYER_Teyvat, update_position=False)

        # MiniMap P:(4451.5, 3113.0) (0.184|0.050), S:wild, D:259.5 (0.949), R:180 (0.498)

        self.minimap_print_log()

    def minimap_print_log(self):
        logger.trace(
            f'MiniMap '
            f'P:({float2str(self.position[0], 4)}, {float2str(self.position[1], 4)}) '
            f'({float2str(self.position_similarity, 3)}|{float2str(self.position_similarity_local, 3)}), '
            f'S:{self.scene}, '
            f'D:{float2str(self.direction, 3)} ({float2str(self.direction_similarity, 3)}), '
            # f'C:{self.channel}, '
            f'R:{self.rotation} ({float2str(self.rotation_confidence)})')

    def update_minimap_domain(self, image):
        """
        Args:
            image:
        """
        self.update_direction(image)
        self.update_rotation(image, layer=MapConverter.LAYER_Domain, update_position=False)

        # MiniMapDomain D:259.5 (0.949), R:180 (0.498)
        logger.trace(
            f'MiniMapDomain '
            f'D:{float2str(self.direction, 3)} ({float2str(self.direction_similarity, 3)}), '
            f'R:{self.rotation} ({float2str(self.rotation_confidence)})')

    @property
    def is_scene_in_wild(self) -> bool:
        return self.scene == 'wild'

    @property
    def is_scene_in_city(self) -> bool:
        return self.scene == 'city'

    def is_position_near(self, position, threshold=1) -> bool:
        diff = np.linalg.norm(np.subtract(position, self.position))
        return diff <= threshold

    def is_direction_near(self, direction, threshold=10) -> bool:
        diff = (self.direction - direction) % 360
        return diff <= threshold or diff >= 360 - threshold

    def is_rotation_near(self, rotation, threshold=10) -> bool:
        diff = (self.rotation - rotation) % 360
        return diff <= threshold or diff >= 360 - threshold

    benchmark_sim = []
    benchmark_loc_sim = []
    def position_benchmark(self):
        self.update_position(itt.capture())
        self.benchmark_sim.append(self.position_similarity)
        self.benchmark_loc_sim.append(self.position_similarity_local)
        logger.trace(f'minimap position benchmark: sim: {round(sum(self.benchmark_sim)/len(self.benchmark_sim),3)},'
                     f'local sim: {round(sum(self.benchmark_loc_sim)/len(self.benchmark_loc_sim),3)}')


if __name__ == '__main__' and False:
    """
    MiniMap 模拟器监听测试
    """
    from source.device.genshin.genshin import Genshin

    device = Genshin('127.0.0.1:16384')
    device.disable_stuck_detection()
    device.screenshot_interval_set(0.3)
    device.screenshot()
    cv2.imshow('123', device.image)
    cv2.waitKey(1)
    minimap = MiniMap(MiniMap.DETECT_Mobile_720p)
    # 从璃月港传送点出发，初始坐标大概大概50px以内就行
    # 坐标位置是 GIMAP 的图片坐标
    minimap.init_position((4580, 3046))
    # 你可以移动人物，GIA会持续监听小地图位置和角色朝向
    while 1:
        device.screenshot()
        minimap.update_minimap(device.image)

if __name__ == '__main__':
    """
    MiniMap windows窗口监听测试
    """
    from source.interaction.capture import WindowsCapture
    import time
    device = WindowsCapture()
    minimap = MiniMap(MiniMap.DETECT_Desktop_1080p)


    if True:
        # 坐标位置是 GIMAP 的图片坐标
        minimap.init_position((2985*2, 2638*2))  # cvat 1334, -4057
        # 你可以移动人物，GIA会持续监听小地图位置和角色朝向
        while 1:
            image = itt.capture()
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # if image.shape != (1080, 1920, 3):
            #     time.sleep(0.3)
            #     continue
            minimap.update_minimap(image)
            # minimap.position_benchmark()
            time.sleep(0.3)
    if False:
        while 1:
            time.sleep(0.1)
            minimap.update_rotation(itt.capture(), update_position=False)
            print(minimap.rotation)
            # minimap.show_rotation(minimap.rotation)
