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
                    [submachine.StringMe() for submachine in self.submachine]
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
        def StringMe(self):
            return 'Title: {}\nStates: \n\t{}\nNotes: {}\n'.format(
                str(self.title),
                '\n\t'.join([state + ' ' + self.states[state].StringMe() for state in self.states]),
                str(self.notes)
                )

    def __init__(self, plantuml_file):
        if os.path.isfile(plantuml_file):
            self.plantuml_file = plantuml_file
        else:
            raise Exception('File {} does not exist.'.format(plantuml_file))

    def CheckUml(self):
        if subprocess.call(['plantuml', '-checkonly', self.plantuml_file]) == 0:
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
        uml_params = self.ParseStateMachineAsDict(uml_text = self.GetUMLText(grouped=True))[0]
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
                    #Remove aliases
                    line = re.sub('state\s+\".*\"\s+as','state', line)
                    #Accumulate all lines that end with \
                    if line.endswith('\\'):
                        accumulated_string += line[:-1]
                    else:
                        if accumulated_string == '':
                            uml_grouped.append(line)
                        else:
                            uml_grouped.append(accumulated_string + line)
                            accumulated_string = ''

                return uml_grouped

    def ParseStateMachineAsDict(self, uml_text, init_line = 0, submachine = False):
        uml_params = self.StateMachineType()
        line_num = init_line
        opening_braces = 0
        closing_braces = 0

        while line_num < len(uml_text):
            line = uml_text[line_num]

            if submachine:
                # Pending to refactor this
                opening_braces += line.count('{')
                closing_braces += line.count('}')
                if closing_braces > opening_braces:
                    break

            # Regex magic yay!
            matchtransition = re.match('(\[\*\]|\w+)(?:|\s+)-->(?:|\s+)(\w+)(?:(?:|\s+)\:(.*))?',line)
            matchstateaction = re.match('(?:state\s+)?(\w+)(?:|\s+)(?:(?:|\s+)\:(.*))?',line)
            matchsubmachine = re.match('(?:state\s+)?(\w+)(?:|\s+)\{.*$',line)

            if line.startswith('title'):
                uml_params.title = line
            elif line.startswith('note'):
                note_match = re.match('.*\"(.*)\"', line)
                if note_match:
                    uml_params.notes.append(self.__LineCleanup(note_match.group(1)))
            elif matchtransition:
                self.__AddTransition(uml_params, matchtransition)
            elif matchsubmachine:
                #Pending to do this in a more elegant way and not depending
                # on the order of the ifs
                state_name = matchstateaction.group(1)
                if uml_params.states.get(state_name) == None:
                    uml_params.states[state_name] = self.StateType()
                sub_info = self.ParseStateMachineAsDict(uml_text, init_line = line_num + 1, submachine = True)
                #Set state name as title
                sub_info[0].title = state_name + '_submachine'
                uml_params.states[state_name].submachine.append(sub_info[0])
                line_num = sub_info[1]
            elif matchstateaction:
                self.__AddStateActions(uml_params, matchstateaction)

            line_num += 1

        return uml_params, line_num

    def __LineCleanup(self, line_string):
        cleaned_string = re.sub(r'(?<!\\)\\n','\n',line_string)
        cleaned_string = cleaned_string.replace('\\\\','\\').strip()
        return cleaned_string

    def __AddTransition(self, uml_params, matchtransition):
        transition = self.TransitionType()
        state_origin = matchtransition.group(1)
        transition.destination = matchtransition.group(2)
        text = matchtransition.group(3)
        if text is not None:
            text = text.split('\\ndo:\\n')
            conditions = text[0]
            transition.conditions = self.__LineCleanup(conditions)
            if len(text) > 1:
                actions = text[1] if text else None
                transition.actions = self.__LineCleanup(actions)
        #transition.actions = matchtransition.group(4)
        #Check if state exits, if not, create it
        if uml_params.states.get(state_origin) == None:
            uml_params.states[state_origin] = self.StateType()
        uml_params.states[state_origin].transitions.append(transition)
        #Also, create destination state if it does not exist
        if uml_params.states.get(transition.destination) == None:
            uml_params.states[transition.destination] = self.StateType()

    def __AddStateActions(self, uml_params, matchstateaction):
        state_name = matchstateaction.group(1)
        actions = matchstateaction.group(2)
        if uml_params.states.get(state_name) == None:
            uml_params.states[state_name] = self.StateType()

        #Get entry, exit and during
        if actions:
            #Do a regex split
            action_matches = re.split(r'(entry\:|during\:|exit\:)', actions)

            #Replace \n by real \n and trim
            action_matches = [self.__LineCleanup(line) for line in action_matches]

            #The list will start with an empty string (or spaces) if it does not match entry
            #any of the keywords. But if it starts with text it is a during
            if action_matches[0].strip() != '':
                uml_params.states[state_name].during = action_matches[0]
            line_num = 1

            while line_num < len(action_matches):
                if action_matches[line_num] == 'entry:':
                    uml_params.states[state_name].entry = action_matches[line_num + 1]
                    line_num += 1
                elif action_matches[line_num] == 'during:':
                    uml_params.states[state_name].during = action_matches[line_num + 1]
                    line_num += 1
                elif action_matches[line_num] == 'exit:':
                    uml_params.states[state_name].exit = action_matches[line_num + 1]
                    line_num += 1
                else:
                    raise Exception('Action {} not recognized.'.format(action_matches[line_num]))
                line_num += 1


    def GenerateFromTemplate(self, output_file, template_file, uml, uml_params):
        env = Environment(
            loader=FileSystemLoader(os.path.dirname(template_file))
        )

        template = env.get_template(os.path.basename(template_file))

        with open(output_file, 'w') as out_file:
            out_file.write(template.render(file_name=output_file, uml=uml,
             uml_params=uml_params, get_submachines=self.GetSubmachineObjects))

    def GetSubmachineObjects(self, uml_object):
        uml_submachines_list = []
        for state in uml_object.states:
            if len(uml_object.states[state].submachine) > 0:
                for uml_submachine in uml_object.states[state].submachine:
                    #Set title of submachine as the name of state parent
                    uml_submachines_list.append(uml_submachine)
                    #Recursion to get more levels
                    uml_submachines_list += self.GetSubmachineObjects(uml_submachine)
        return uml_submachines_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process PlantUML file to generate code')
    parser.add_argument('--input','-i', required = True, dest = 'plantuml_file',
                        help ='Plant UML file from which to generate code')
    parser.add_argument('--output','-o', required = True, dest = 'output_files',
                        help ='Code file generated. Separate by comma in case of'
                        'more than one template')
    parser.add_argument('--templates', '-t', dest = 'templates', default = 'templates/C_code.c,templates/C_code.h',
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
