# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "glTF Export Custom Node Name",
    "author": "todashuta",
    "version": (1, 2, 0),
    "blender": (2, 93, 0),
    "location": "3D View > Side Bar > Item > glTF Export Custom Node Name",
    "description": "glTF出力で重複した名前のオブジェクト（ノード）を出力可能にします",
    "warning": "アニメーションやシェイプキーなどが複雑な場合は問題が起こるかもしれません（未確認）",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}


import bpy


# def __gather_name(blender_object, export_settings):
#     #print(">>>", blender_object)
#     if blender_object.gltf_export_name != "":
#         return blender_object.gltf_export_name
#     return blender_object.name
# 
# # overwrite private function... any better way?
# import io_scene_gltf2.blender.exp.gltf2_blender_gather_nodes
# io_scene_gltf2.blender.exp.gltf2_blender_gather_nodes.__gather_name = __gather_name


class GLTF_EXPORT_CUSTOM_NODE_NAME_PT_panel(bpy.types.Panel):
    bl_label = "glTF Export Custom Node Name"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        if context.active_object:
            layout.prop(context.active_object, "gltf_export_name")
        else:
            layout.label(icon="INFO", text="Active Object is None")


class GLTF_EXPORT_CUSTOM_NODE_NAME_STAT_PT_panel(bpy.types.Panel):
    bl_label = "Statistics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_context = "objectmode"
    bl_parent_id = "GLTF_EXPORT_CUSTOM_NODE_NAME_PT_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        from collections import Counter

        layout = self.layout
        objects = [ob for ob in context.visible_objects if ob.gltf_export_name != ""]
        counter = Counter([ob.gltf_export_name for ob in objects])
        col = layout.column(align=True)
        for k,v in sorted(counter.items()):
            split = col.split(align=True, factor=0.6)
            split.label(text=f"{k}", icon="OBJECT_DATA")
            split.label(text=f"{v}")
            op = split.operator(GLTF_EXPORT_CUSTOM_NODE_NAME_OT_select_by_name.bl_idname, text="", icon="SELECT_SET")
            op.name = k


class GLTF_EXPORT_CUSTOM_NODE_NAME_OT_select_by_name(bpy.types.Operator):
    bl_idname = "object.gltf_export_custom_node_name_select_by_name"
    bl_label = "Select by Name"
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty(name="Name", default="")

    shift_key_down = False

    @classmethod
    def poll(cls, context):
        return True

    @classmethod
    def description(cls, context, properties) -> str:
        desc = "\n".join([
                f"カスタムノード名に {properties.name} が設定されたオブジェクトを選択します",
                "Shiftを押しながらクリックで現在の選択に追加します"])
        return desc

    def invoke(self, context, event):
        self.shift_key_down = event.shift
        return self.execute(context)

    def execute(self, context):
        if not self.shift_key_down:
            bpy.ops.object.select_all(action='DESELECT')

        for ob in context.selectable_objects:
            if ob.gltf_export_name == self.name:
                ob.select_set(True)

        return {"FINISHED"}


classes = (
        GLTF_EXPORT_CUSTOM_NODE_NAME_PT_panel,
        GLTF_EXPORT_CUSTOM_NODE_NAME_STAT_PT_panel,
        GLTF_EXPORT_CUSTOM_NODE_NAME_OT_select_by_name,
)


class glTF2ExportUserExtension:

    def __init__(self):
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.enabled = bpy.context.scene.gltf_export_custom_node_name_enabled

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        if not self.enabled:
            return  # do nothing
        if blender_object.gltf_export_name == "":
            return  # do nothing
        gltf2_object.name = blender_object.gltf_export_name
        print("[glTF Export Custom Node Name]", blender_object.name, "->", gltf2_object.name)


class GLTF_EXPORT_CUSTOM_NODE_NAME_PT_filebrowser_panel(bpy.types.Panel):

    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Use Custom Node Name"
    bl_parent_id = "GLTF_PT_export_user_extensions"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf"

    def draw_header(self, context):
        scene = bpy.context.scene
        self.layout.prop(scene, "gltf_export_custom_node_name_enabled", text="")

    def draw(self, context):
        layout = self.layout
        if context.scene.gltf_export_custom_node_name_enabled:
            layout.label(text="カスタムノード名で出力されます。", icon="INFO")


def register():
    bpy.types.Scene.gltf_export_custom_node_name_enabled = bpy.props.BoolProperty(
            name="Use Custom Node Name", default=False, description="カスタムノード名出力を有効にします。\n（glTF Export Custom Node Name Addon）")
    bpy.types.Object.gltf_export_name = bpy.props.StringProperty(
            name="Name", default="",
            description="glTF出力時のオブジェクト名（ノード名）\n空のときはオブジェクト名を使用\n他と重複してもよい")

    for cls in classes:
        bpy.utils.register_class(cls)


def register_panel():
    try:
        bpy.utils.register_class(GLTF_EXPORT_CUSTOM_NODE_NAME_PT_filebrowser_panel)
    except Exception:
        pass

    return unregister_panel


def unregister_panel():
    try:
        bpy.utils.unregister_class(GLTF_EXPORT_CUSTOM_NODE_NAME_PT_filebrowser_panel)
    except Exception:
        pass


def unregister():
    unregister_panel()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.gltf_export_custom_node_name_enabled
    del bpy.types.Object.gltf_export_name


if __name__ == "__main__":
    register()
