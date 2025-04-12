import folder_paths
import trimesh as Trimesh

mesh_extensions = ['.glb', '.gltf', '.obj', '.ply', '.stl']
output_dir = folder_paths.get_output_directory()
all_files, _ = folder_paths.recursive_search(output_dir)
file_list = folder_paths.filter_files_extensions(all_files, mesh_extensions)
files = []

class Load3DMesh:
    @classmethod
    def INPUT_TYPES(s):
        for file in file_list:
            rel_path = file
            files.append(rel_path)

        return {
            "required": {
                "mesh": (sorted(files),), 
            }
        }
    
    RETURN_TYPES = ("TRIMESH", "STRING",)
    RETURN_NAMES = ("trimesh", "mesh_path",)
    
    FUNCTION = "load"
    CATEGORY = "NCNodes/3D"
    DESCRIPTION = "List 3D files in the output folder and loads selected file as trimesh."
    EXPERIMENTAL = True # Need to find a way to refresh the list of files if anything changes in the output directory

    def load(self, mesh):
        mesh_file = folder_paths.get_annotated_filepath(mesh, output_dir)
        trimesh = Trimesh.load(mesh_file, force="mesh")
        return (trimesh, mesh_file,)