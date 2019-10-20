import argparse, subprocess, os, re
from jinja2 import Environment, FileSystemLoader

class PlantUMLCodeGeneration():

    class StateType():
        def __init__(self):
            self.entry = None
            self.during = None
            self.exit = None
            self.transitions = []
            self.submachine = []
        def StringMe(self):
            return 'Entry: {} During: {} Exit: {} Transitions : {} Submachines: {}'.format(
                    str(self.entry),
                    str(self.during),
                    str(self.exit),
                    [transition.StringMe() for transition in self.transitions],
                    str(self.submachine)
                    )

    class TransitionType():
        def __init__(self):
            self.destination = None
            self.conditions = None
            self.actions = None
        def StringMe(self):
            return 'Destination: {} Condition: {} Action: {}'.format(
                str(self.destination),
                str(self.conditions),
                str(self.actions)
                )

    class StateMachineType():
        def __init__(self):
            self.title = None
            self.states = {}
            self.notes = []

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

    def GenerateCode(self, output_files, templates, no_check = False):

        if (no_check == False):
            if self.CheckUml() == False:
                raise Exception('File {} contains UML errors.'.format(self.plantuml_file))

        uml, uml_params = self.ParseStateMachine()

        if len(output_files) == len(templates):
            for out_file, template in zip(output_files, templates):
                self.GenerateFromTemplate(out_file, template, uml, uml_params)
        else:
            raise Exception('Number of template and output files don\'t match.')

    def ParseStateMachine(self):
        uml = self.GetUMLText()
        uml_params = self.ParseStateMachineAsDict()
        return uml, uml_params

    def GetUMLText(self, grouped = False):
        with open(self.plantuml_file, 'r') as plantuml_file:
            uml = plantuml_file.readlines()
            if grouped == False:
                return uml
            else:
                #Group all strings containing \ at the end
                uml_grouped = []
                accumulated_string = ''
                for line in uml:
                    #First strip the line to forget about leading and trailing
                    #spaces
                    line = line.strip()
                    if line.endswith('\\'):
                        accumulated_string += line[:-1]
                    else:
                        if accumulated_string == '':
                            uml_grouped.append(line)
                        else:
                            uml_grouped.append(accumulated_string + line)
                            accumulated_string = ''
                return uml_grouped

    def ParseStateMachineAsDict(self):
        uml_params = self.StateMachineType()

        uml_text = self.GetUMLText(grouped=True)

        for line in uml_text:
            matchtransition = re.match('(\[\*\]|\w+)(?:|\s+)-->(?:|\s+)(\w+)(?:(?:|\s+)\:(.*))?',line)
            matchstateaction = re.match('(?:state\s+)?\s+(\w+)(?:|\s+)(?:(?:|\s+)\:(.*))?',line)
            if line.startswith('title'):
                uml_params.title = line
                continue
            elif matchtransition:
                self.__AddTransition(uml_params, matchtransition)
            elif matchstateaction:
                self.__AddStateActions(uml_params, matchstateaction)


        for state in uml_params.states:
            print(state.upper(), uml_params.states[state].StringMe())

        return uml_params

    def __AddTransition(self, uml_params, matchtransition):
        transition = self.TransitionType()
        state_origin = matchtransition.group(1)
        transition.destination = matchtransition.group(2)
        transition.conditions = matchtransition.group(3)
        #transition.actions = matchtransition.group(4)
        #Check if state exits, if not, create it
        if uml_params.states.get(state_origin) == None:
            uml_params.states[state_origin] = self.StateType()
        uml_params.states[state_origin].transitions.append(transition)

    def __AddStateActions(self, uml_params, matchstateaction):
        state_origin = matchstateaction.group(1)
        if uml_params.states.get(state_origin) == None:
            uml_params.states[state_origin] = self.StateType()

    def GenerateFromTemplate(self, output_file, template_file, uml, uml_params):
        env = Environment(
            loader=FileSystemLoader('templates')
        )

        template = env.get_template(template_file)

        with open(output_file, 'w') as out_file:
            out_file.write(template.render(file_name=output_file, uml=uml))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process PlantUML file to generate code')
    parser.add_argument('--input','-i', required = True, dest = 'plantuml_file',
                        help ='Plant UML file from which to generate code')
    parser.add_argument('--output','-o', required = True, dest = 'output_files',
                        help ='Code file generated. Separate by comma in case of'
                        'more than one template')
    parser.add_argument('--templates', '-t', dest = 'templates', default = 'C_code.c,C_code.h',
                        help = 'Templates to be used separated by comma')
    parser.add_argument('--no-check', action = 'store_true',
                        help = 'This option is strongly discouraged. With this option'
                        'you are defining to not check that your PlantUML is valid.')

    args = parser.parse_args()

    plantuml_obj = PlantUMLCodeGeneration(args.plantuml_file)
    #Transform templates to list
    template_files = args.templates.split(',')
    output_files = args.output_files.split(',')
    plantuml_obj.GenerateCode(output_files, template_files)
