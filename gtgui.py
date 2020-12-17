from geotag_obj import Project

project = Project()
project.create(inputPath=r'C:\Users\beck\Documents\CSCR\geotag-tool-python\July31', projectPath=r'C:\Users\beck\Documents\CSCR\geotag-tool-python\July31')
project.match(timeoffset=4)
project.export()