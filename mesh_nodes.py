import folder_paths
import trimesh as Trimesh

mesh_extensions = ['.glb', '.gltf', '.obj', '.ply', '.stl']
output_dir = folder_paths.get_output_directory()

def get_mesh_files():
    all_files, _ = folder_paths.recursive_search(output_dir)
    return folder_paths.filter_files_extensions(all_files, mesh_extensions)

def get_afilepath(path):
    return folder_paths.get_annotated_filepath(path, output_dir)

def load_trimesh(mesh_file):
    return Trimesh.load(mesh_file, force="mesh")

class Load3DMesh:
    @classmethod
    def INPUT_TYPES(s):
        files = sorted(get_mesh_files())

        return {
            "required": {
                "mesh": (files,), 
            }
        }
    
    RETURN_TYPES = ("TRIMESH", "STRING",)
    RETURN_NAMES = ("trimesh", "mesh_path",)
    
    FUNCTION = "load"
    CATEGORY = "NCNodes/3D"
    DESCRIPTION = """
List 3D files in the output folder and loads selected file as trimesh.
When new files are added or removed from the output directory
press R to refresh the node definitions.
"""

    def load(self, mesh):
        mesh_file = get_afilepath(mesh)
        trimesh = load_trimesh(mesh_file)
        return (trimesh, mesh_file,)