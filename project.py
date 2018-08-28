import os
import sys
import json

class ml_project:
    dataDir = 'data'
    logDir = 'log'
    modelDir = 'model'
    scriptDir = 'script'
    resultDir = 'result'
    def __init__(self):
        # default dirs
        self.projectName = None
        self.projectFile = None  # one file
        self.projectDir = None  # dir
        self.description = None  # save in file
        self.model = list()  # save each model class

        self.modelFiles = list() # *.md
        self.scriptFiles = list()  # python or jupyter notebook script list
        self.imageDirs = list()
        self.pythonScripts = list()
        self.resultFiles = list()  # running result files list
        self.logFiles = list()  # log files for each run
        self.dataFiles_csv = list()  # csv data file list
        self.dataFiles_pkl = list()  # pkl data file list
        self.describe_map = dict()  # dict save description of each data(csv, pkl), script(python,ipython)

    @classmethod
    def initProject(cls, project_dir):
        if not os.path.isdir(project_dir):
            raise Exception(project_dir, 'is not a dir')
        newProject = ml_project()
        newProject.projectDir = project_dir

        # search data files
        files = os.listdir(os.path.join(project_dir, newProject.dataDir))
        for filename in files:
            if not os.path.isdir(filename):
                if filename.endswith('.pkl'):
                    newProject.dataFiles_pkl.append(os.path.abspath(os.path.join(project_dir, newProject.dataDir, filename)))
                if filename.endswith('.csv'):
                    newProject.dataFiles_csv.append(os.path.abspath(os.path.join(project_dir, newProject.dataDir, filename)))
        # search script files
        files = os.listdir(os.path.join(project_dir, newProject.scriptDir))
        for filename in files:
            if not os.path.isdir(filename):
                if filename.endswith('.py'):
                    newProject.pythonScripts.append(os.path.abspath(os.path.join(project_dir, newProject.scriptDir, filename)))
                    newProject.scriptFiles.append(os.path.abspath(os.path.join(project_dir, newProject.scriptDir, filename)))
                if filename.endswith('.ipynb'):
                    newProject.scriptFiles.append(os.path.abspath(os.path.join(project_dir, newProject.scriptDir, filename)))
        # search log files
        files = os.listdir(os.path.join(project_dir, newProject.logDir))
        for filename in files:
            if not os.path.isdir(filename):
                if filename.endswith('.log'):
                    newProject.logFiles.append(os.path.abspath(os.path.join(project_dir, newProject.logDir, filename)))
        # search result files
        files = os.listdir(os.path.join(project_dir, newProject.resultDir))
        for filename in files:
            if not os.path.isdir(filename):
                if filename.endswith('.mlr'):
                    newProject.resultFiles.append(os.path.abspath(os.path.join(project_dir, newProject.resultDir, filename)))
        # search model files
        files = os.listdir(os.path.join(project_dir, newProject.modelDir))
        for filename in files:
            if not os.path.isdir(filename):
                if filename.endswith('.md'):
                    newProject.modelFiles.append(os.path.abspath(os.path.join(project_dir, newProject.modelDir, filename)))
        newProject.description = os.path.abspath(os.path.join(project_dir, 'description.ml'))
        return newProject

    @classmethod
    def loadProject(cls, projectFile):
        with open(projectFile, 'r') as f:
            projectDict = json.load(f)
            newProject = ml_project()
            newProject.projectName = projectDict['projectName']
            newProject.projectDir = projectDict['projectDir']
            newProject.projectFile = projectDict['projectFile']
            newProject.description = projectDict['description']
            newProject.modelFiles = projectDict['modelFiles']
            newProject.scriptFiles = projectDict['scriptFiles']
            newProject.imageDirs = projectDict['imageDirs']
            newProject.resultFiles = projectDict['resultFiles']
            newProject.logFiles = projectDict['logFiles']
            newProject.dataFiles_csv = projectDict['dataFiles_csv']
            newProject.dataFiles_pkl = projectDict['dataFiles_pkl']
            newProject.describe_map = projectDict['describe_map']
            return newProject

    def dumpProject(self, projectFile):
        projectDict = dict()
        projectDict['projectName'] = self.projectName
        projectDict['projectDir'] = self.projectDir
        projectDict['projectFile'] = self.projectFile
        projectDict['description'] = self.description
        projectDict['modelFiles'] = self.modelFiles
        projectDict['scriptFiles'] = self.scriptFiles
        projectDict['imageDirs'] = self.imageDirs
        projectDict['resultFiles'] = self.resultFiles
        projectDict['logFiles'] = self.logFiles
        projectDict['dataFiles_csv'] = self.dataFiles_csv
        projectDict['dataFiles_pkl'] = self.dataFiles_pkl
        projectDict['describe_map'] = self.describe_map
        with open(os.path.join(self.projectDir, projectFile), 'w') as f:
            json.dump(projectDict, f)


if __name__ == '__main__':
    p = ml_project()
    project_dir = 'E:/project/House Prices'
    #p.initProject(project_dir)
    p.loadProject(os.path.join())
