""" Create 3d Earth map and add lat/lon data. """
import bpy
import bmesh
import numpy as np
import pandas as pd
from bpy import context, data, ops
from math import sin, cos, radians, pi, atan, tan

EARTH_IMAGE = "D:\\EARTH_MAPS\\8081_earthmap4k.jpg" # Substitute with your local path
EARTH_BUMP = "D:\\EARTH_MAPS\\8081_earthbump4k.jpg" # Substitute with your local path
DATA_PATH = r'YOUR_PATH_TO\coordiante_data.gzip'    # Substitute with your local path

def latlonger(lat_deg, lon_deg):
    """
        Converts lat/lon coordinates to xyz for 3d plotting
		Credit to > https://blender.stackexchange.com/questions/36837/convert-csv-latitude-longtitude-to-blender-coordinates/36843#36843
    """
    lat = radians(lat_deg)
    lon = radians(lon_deg)
    # see: http://www.mathworks.de/help/toolbox/aeroblks/llatoecefposition.html
    alt = 0.01
    rad = 100 # radius of sphere in BUs
    f  = 0.0  # flattening
    ls = atan((1 - f)**2 * tan(lat))  # lambda
    x = rad * cos(lat) * cos(lon) + alt * cos(lat) * cos(lon)
    y = rad * cos(lat) * sin(lon) + alt * cos(lat) * sin(lon)
    z = rad * sin(lat) + alt * sin(lat)
    return (x, y, z)


# Delete all existing items in scene.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Add a sphere, set quality to highest and apply shade smooth. Scale 'semi' adjusted to coordinate conversion and raised 100m above. 
bpy.ops.mesh.primitive_uv_sphere_add(enter_editmode=False, align='WORLD', location=(0, 0, 100), scale=(202, 202, 202))
bpy.ops.object.modifier_add(type='SUBSURF')
bpy.context.object.modifiers["Subdivision"].quality = 6
bpy.context.object.modifiers["Subdivision"].levels = 6
bpy.context.object.modifiers["Subdivision"].render_levels = 6
bpy.ops.object.modifier_apply(modifier="Subdivision")
bpy.ops.object.shade_smooth()

# Create a new material
material = bpy.data.materials.new(name="EarthMaterial")
# Use nodes
material.use_nodes = True
# Add Principled BSDF
bsdf = material.node_tree.nodes["Principled BSDF"]
texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
# Load image of Earth
texImage.image = bpy.data.images.load(EARTH_IMAGE)
# Set node links for color
material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

# Select Material Output node
bsdf = material.node_tree.nodes["Material Output"]
texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
# Load image of Earth bump version
texImage.image = bpy.data.images.load(EARTH_BUMP)
# Set colorspace to Non-Color
texImage.image.colorspace_settings.name = 'Non-Color'
# Add the Bump node
bump_shader = material.node_tree.nodes.new('ShaderNodeBump')
# Set node links for displacement
material.node_tree.links.new(bsdf.inputs['Displacement'], bump_shader.outputs['Normal'])
# Set node links for color from bump node
material.node_tree.links.new(bump_shader.inputs['Normal'], texImage.outputs['Color'])
# Activate the sphere object
ob = context.view_layer.objects.active
# Set Metallic to 1
bpy.data.materials["EarthMaterial"].node_tree.nodes["Principled BSDF"].inputs[4].default_value = 1
# Assign it to object
ob.data.materials.append(material)

# Import data containing coordinates.
# You can read from any filetypes pandas provides. I just happen to use parquet
coordinate_data = pd.read_parquet(DATA_PATH)

for i, r in coordinate_data.iterrows():
    # Convert coordinates. Switch column names if needed.
    c = latlonger(r['LAT'], r['LON'])
    # Add sphere mesh with xyz
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.2, location=(c[0], c[1], 100+c[2]))
    # Add Subsurf modifier and smoothen mesh
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers['Subdivision'].render_levels = 2
    bpy.context.object.modifiers['Subdivision'].levels = 1
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_apply(modifier="Subdivision")
    
# Add the Sun. Postion and Rotiation set.    
bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 300, 250), rotation=(1.0472, 1.5708, 2.61799), scale=(1, 1, 1))
# Set sun intensity
bpy.context.object.data.energy = 8
# Set sun angle
bpy.context.object.data.angle = 0

# Add camera and set postion to focus on full earth view
bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(519.28, 87.7087, 74.2635), rotation=(1.61169, -0.0422343, 1.71535), scale=(1, 1, 1))
