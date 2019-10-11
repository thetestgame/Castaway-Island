from panda3d.core import TextNode, load_prc_file_data, Shader
from panda3d.core import AntialiasAttrib, VBase3, VBase4, Vec3
from panda3d.core import Material, CardMaker, Fog, DirectionalLight
from panda3d.core import AmbientLight, BoundingVolume

from direct.showbase.ShowBase import ShowBase
from direct.interval.IntervalGlobal import Parallel, Sequence
from direct.interval.LerpInterval import LerpFunc
from direct.gui.OnscreenText import OnscreenText

import sys

load_prc_file_data("", "window-title Panda3D Castaway Castaway Island")
load_prc_file_data("", "framebuffer-srgb #t")
load_prc_file_data("", "default-fov 90")
load_prc_file_data("", "gl-version 3 2")
load_prc_file_data("", "framebuffer-multisample 1")
load_prc_file_data("", "multisamples 1")
load_prc_file_data("", "sync-video #f")

SKY_COLOR = VBase3(135 / 255.0, 206 / 255.0, 235 / 255.0)
SUN_TEMPERATURE = 5000

# Function to put instructions on the screen.
def add_instructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

# Function to put title on the screen.
def add_title(text):
    return OnscreenText(text=text, style=1, fg=(1,1,1,1),
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .07)

class CastawayBase(ShowBase):
    """
    The Showbase instance for the castaway example.
    Handles window and scene management
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Position the camera.  Set a saner far distance.
        self.camera.set_pos(-35, -6, 6)
        self.camera.set_hpr(-74, -19, 91)
        self.camLens.set_far(250)
        self.disable_mouse()

        # Display instructions
        add_title("Panda3D Tutorial: Castaway Island")
        add_instructions(0.95, "[ESC]: Quit")
        add_instructions(0.90, '[TAB]: Toggle Buffer Viewer')
        add_instructions(0.85, '[F12]: Save Screenshot')
        add_instructions(0.80, '[F11]: Toggle Frame Rate Meter')
        add_instructions(0.75, '[F]: Toggle Sun Frustum')
        add_instructions(0.70, '[O]: Toggle OOBE mode')
        add_instructions(0.65, '[1]: Enable static adjustment mode')
        add_instructions(0.60, '[2]: Enable dynamic adjustment mode')
        add_instructions(0.55, '[3]: disable automatic adjustment')

        # Prepare scene graph
        self.scene_root = self.render.attach_new_node('castaway_scene')
        scene_shader = Shader.load(
            Shader.SL_GLSL, 
            "resources/scene.vert", 
            "resources/scene.frag")
        self.render.set_shader(scene_shader)
        self.render.set_shader_input('camera', self.camera)
        self.render.set_antialias(AntialiasAttrib.MAuto)

        # Load the island asset
        self.island = self.loader.load_model('resources/island')
        self.island.reparent_to(self.scene_root)
        self.island.set_p(90)
        self.island.flatten_strong()

        # Create water and fog instances
        self.load_water()
        self.load_fog()

        # Setup lighting
        self.load_lights()
        self.show_frustum = False
        self.taskMgr.add(self._adjust_lighting_bounds_task, sort=45)

        self.adjustment_mode = 0

        # Setup key bindings for debuging
        self.accept('tab', self.bufferViewer.toggleEnable)
        self.accept('f12', self.screenshot)
        self.accept('o', self.oobe)
        self.accept('f11', self.toggle_frame_rate_meter)
        self.accept('1', self.set_adjust_mode, [0])
        self.accept('2', self.set_adjust_mode, [1])
        self.accept('3', self.set_adjust_mode, [2])
        self.accept('f', self.toggle_frustum)
        self.accept('esc', sys.exit)

    def set_adjust_mode(self, mode):
        """
        Sets the currently enabled adjustment mode
        """

        if mode < 0 or mode > 2:
            mode = 0

        print('Setting adjustment mode: %s' % mode)
        self.adjustment_mode = mode

    def toggle_frustum(self):
        """
        Toggles the sun lights frustum viewer
        """

        if self.show_frustum:
            self.sun_light.hide_frustum()
        else:
            self.sun_light.show_frustum()

        self.show_frustum = not self.show_frustum

    def toggle_frame_rate_meter(self):
        """
        Toggles the frame rate meter's state
        """

        self.set_frame_rate_meter(self.frameRateMeter == None)

    def load_water(self):
        """
        Loads the islands psuedo infinite water plane
        """

        # Create a material for the PBR shaders
        water_material = Material()
        water_material.set_base_color(VBase4(0, 0.7, 0.9, 1))

        water_card_maker = CardMaker('water_card')
        water_card_maker.set_frame(-200, 200, -150, 150)
        self.water_path = self.render.attach_new_node(water_card_maker.generate())
        self.water_path.set_material(water_material, 1)
        self.water_path.set_scale(500)

    def load_fog(self):
        """
        Loads the fog seen in the distance from the island
        """

        self.world_fog = Fog('world_fog')
        self.world_fog.set_color(Vec3(SKY_COLOR.get_x(), SKY_COLOR.get_y(), SKY_COLOR.get_z()))
        self.world_fog.set_linear_range(0, 320)
        self.world_fog.set_linear_fallback(45, 160, 320)
        self.world_fog_path = self.render.attach_new_node(self.world_fog)
        self.render.set_fog(self.world_fog)

    def load_lights(self):
        """
        Loads the scene lighting objects
        """

        # Create a sun source
        self.sun_light = DirectionalLight('sun_light')
        self.sun_light.set_color_temperature(SUN_TEMPERATURE)
        self.sun_light.color = self.sun_light.color * 4
        self.sun_light_path = self.render.attach_new_node(self.sun_light)
        self.sun_light_path.set_pos(10, -10, -10)
        self.sun_light_path.look_at(0, 0, 0)
        self.sun_light_path.hprInterval(
            10.0, (
                self.sun_light_path.get_h(), 
                self.sun_light_path.get_p() - 360, 
                self.sun_light_path.get_r()), 
            bakeInStart=True).loop()
        self.render.set_light(self.sun_light_path)

        self.sun_light.get_lens().set_near_far(1, 30)
        self.sun_light.get_lens().set_film_size(20, 40)
        self.sun_light.set_shadow_caster(True, 4096, 4096)

        # Create a sky light
        self.sky_light = AmbientLight('sky_light')
        self.sky_light.set_color(VBase4(SKY_COLOR * 0.04, 1))
        self.sky_light_path = self.render.attach_new_node(self.sky_light)
        self.render.set_light(self.sky_light_path)
        self.set_background_color(SKY_COLOR)

    def adjust_colors(self, color):
        """
        Adjusts the scene's current time of day
        """
        
        self.set_background_color(color)
        self.sky_light.set_color(color)
        self.world_fog.set_color(color)

    def adjust_lighting_static(self):
        """
        This method tightly fits the light frustum around the entire scene.
        Because it is computationally expensive for complex scenes, it is
        intended to be used for non-rotating light sources, and called once at
        loading time.
        """

        bmin, bmax = self.scene_root.get_tight_bounds(self.sun_light_path)
        lens = self.sun_light.get_lens()
        lens.set_film_offset((bmin.xz + bmax.xz) * 0.5)
        lens.set_film_size(bmax.xz - bmin.xz)
        lens.set_near_far(bmin.y, bmax.y)

    def adjust_lighting_dynamic(self):
        """
        This method is much faster, but not nearly as tightly fitting.  May (or
        may not) work better with "bounds-type best" in Config.prc.
        
        It will automatically try to reduce the shadow frustum size in order not
        to shadow objects that are out of view.  Additionally, it will disable
        the shadow camera if the scene bounds are completely out of view of the
        shadow camera.
        """

        # Get Panda's precomputed scene bounds.
        scene_bounds = self.scene_root.get_bounds()
        scene_bounds.xform(self.scene_root.get_mat(self.sun_light_path))

        # Also transform the bounding volume of the camera frustum to light space.
        lens_bounds = self.camLens.make_bounds()
        lens_bounds.xform(self.camera.get_mat(self.sun_light_path))

        # Does the lens bounds contain the scene bounds?
        intersection = lens_bounds.contains(scene_bounds)
        if not intersection:
            # No; deactivate the shadow camera.
            self.sun_light.set_active(False)
            return

        self.sun_light.set_active(True)
        bmin = scene_bounds.get_min()
        bmax = scene_bounds.get_max()

        if intersection & BoundingVolume.IF_all:
            # Completely contains the world volume; no adjustment necessary.
            pass
        else:
            # Adjust all dimensions to tighten around the view frustum bounds,
            # except for the near distance, because objects that are out of view
            # in that direction may still cast shadows.
            lmin = lens_bounds.get_min()
            lmax = lens_bounds.get_max()

            bmin[0] = min(max(bmin[0], lmin[0]), lmax[0])
            bmin[1] = min(bmin[1], lmax[1])
            bmin[2] = min(max(bmin[2], lmin[2]), lmax[2])

        lens = self.sun_light.get_lens()
        lens.set_film_offset((bmin.xz + bmax.xz) * 0.5)
        lens.set_film_size(bmax.xz - bmin.xz)
        lens.set_near_far(bmin.y, bmax.y)

    def _adjust_lighting_bounds_task(self, task):
        """
        Calls the adjust_lighting_bounds function between the ivalLoop(20) and the igLoop(50)
        """

        if self.adjustment_mode == 0:
            self.adjust_lighting_static()
        elif self.adjustment_mode == 1:
            self.adjust_lighting_dynamic()

        return task.cont

base = CastawayBase()
base.run()