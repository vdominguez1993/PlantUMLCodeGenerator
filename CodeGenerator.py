import argparse, subprocess, os
from jinja2 import Environment, FileSystemLoader

class PlantUMLCodeGeneration():
    def __init__(self, plantuml_file):
        if os.path.isfile(plantuml_file):
            self.plantuml_file = plantuml_file
        else:
            raise Exception('File {} does not exist.'.format(plantuml_file))

    def CheckUml(self):
        if subprocess.call(['plantuml',self.plantuml_file]) == 0:
            return True
        else:
            return False

    def GenerateCode(self, output_file, no_check = False):

        if (no_check == False):
            if self.CheckUml() == False:
                raise Exception('File {} contains UML errors.'.format(self.plantuml_file))

        uml = self.ParseStateMachineAsDict()
        self.GenerateCFile(output_file, uml)

    def ParseStateMachineAsDict(self):
        with open(self.plantuml_file, 'r') as plantuml_file:
            uml = plantuml_file.readlines()
        return uml

    def GenerateCFile(self, output_file, uml):
        env = Environment(
            loader=FileSystemLoader('templates')
        )
        template = env.get_template('C_code.tmpl')
        print(template.render(file_name=output_file, uml=uml))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process PlantUML file to generate code')
    parser.add_argument('--input','-i', required = True, dest = 'plantuml_file',
                        help ='Plant UML file from which to generate code')
    parser.add_argument('--output','-o', required = True, dest = 'output_file',
                        help ='Code file generated')
    parser.add_argument('--language', '-l', dest = 'language', default = 'C',
                        help = 'Language to be used, only C supported for the moment')
    parser.add_argument('--no-check', action = 'store_true',
                        help = 'This option is strongly discouraged. With this option'
                        'you are defining to not check that your PlantUML is valid.')

    args = parser.parse_args()

    plantuml_obj = PlantUMLCodeGeneration(args.plantuml_file)
    plantuml_obj.GenerateCode(args.output_file)
