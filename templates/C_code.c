/**
 * @file {{file_name}}
{% for n in uml %} * {{n}}{% endfor %} *
 **/
{#- Jinja function calls and variables #}
{%- set fsm_name = file_name.replace('.c','') %}
{%- set submachines_list = get_submachines(uml_params) %}


#include "{{file_name.replace('.c','.h')}}"
#include <time.h>
#include <stdint.h>
#include <stdio.h>

{#> Includes #}
{%- for note in uml_params.notes %}
{%- if note.startswith('Includes:') %}
{%- for line in note.split('\n')[1:] %}
#include "{{line}}"
{%- endfor %}
{%- endif %}
{%- endfor %}

{#> Defines #}
{%- for note in uml_params.notes %}
{%- if note.startswith('Defines:') %}
{%- for line in note.split('\n')[1:] %}
#define {{line}}
{%- endfor %}
{%- endif %}
{%- endfor %}

static t_states_{{fsm_name}} {{fsm_name}}_state = STATE_{{fsm_name.upper()}}_INITIAL;
{% for submachine in submachines_list %}
static t_states_{{submachine.title}} {{submachine.title}}_state = STATE_{{submachine.title.upper()}}_INITIAL;
{%- endfor %}

static int delay = 0;

{% for submachine in submachines_list %}
static int delay_{{submachine.title.lower().replace('_submachine','')}} = 0;
{%- endfor %}

{# Submachine function prototypes #}
{% for submachine in submachines_list %}
/*** Submachine prototypes for task and init ***/
static void {{submachine.title}}_initialize( void );

static void {{submachine.title}}_task( void );
{% endfor %}

{%- macro function_prototypes(fsm_name, uml_params) %}
    {#- States function prototypes #}
    {%- for state in uml_params.states %}
        {%- if state == '[*]' %}
static void {{fsm_name}}_initial_state( void );
        {%- else %}
static void {{state.lower()}}( void );
        {%- endif %}
    {% endfor %}
{%- endmacro %}

/*** State prototypes for {{fsm_name}} ***/
{{function_prototypes(fsm_name, uml_params)}}
{%- for submachine in submachines_list %}
/*** State prototypes for {{submachine.title}} ***/
{{function_prototypes(submachine.title, submachine)}}
{%- endfor %}

{%- macro core_code_implementation(fsm_name, uml_params, delay_name, is_main = true) %}
{{'' if is_main else 'static '}}void {{fsm_name}}_initialize( void ){
    {{fsm_name}}_state = STATE_{{fsm_name.upper()}}_INITIAL;
}

{{'' if is_main else 'static '}}void {{fsm_name}}_task( void ){

    static struct timespec last_time;
    struct timespec current_time;

    (void) clock_gettime(CLOCK_MONOTONIC, &current_time);
    {{delay_name}} += current_time.tv_sec - last_time.tv_sec;
    last_time = current_time;

    switch ({{fsm_name}}_state){
{%- for state in uml_params.states %}
    {#- Exception for initial state #}
    {%- if state == '[*]' %}
        case STATE_{{fsm_name.upper()}}_INITIAL:
            {{fsm_name}}_initial_state();
    {%- else %}
        case STATE_{{fsm_name.upper()}}_{{state.upper()}}:
            {{state.lower()}}();
    {%- endif %}
            break;
{%- endfor %}
        default:
            {{fsm_name}}_state = STATE_{{fsm_name.upper()}}_INITIAL;
            break;
    }
}
{%- endmacro %}

{%- macro function_implementation(fsm_name, uml_params, delay_name) %}
{% for state in uml_params.states %}
{%- if state == '[*]' %}
static void {{fsm_name}}_initial_state( void ){
{%- else %}
static void {{state.lower()}}( void ){
{%- endif %}

    {%- if uml_params.states[state].during is not none %}
    {{uml_params.states[state].during|indent(4,false)}}
    {%- endif %}

    {%- if uml_params.states[state].submachine != [] %}
    {%- for submachine in uml_params.states[state].submachine %}
    {{submachine.title + '_task();'}}
    {%- endfor %}
    {%- endif %}

    {%- for transition in uml_params.states[state].transitions %}
    {%- set indentation_level = 4 %}
    {%- if transition.conditions is not none %}
    {%- set indentation_level = 8 %}
    if ({{transition.conditions|indent(6,false)}}) {
    {%- endif %}
        {%- if transition.actions is not none %}
{{transition.actions|indent(indentation_level,true)}}
        {%- endif %}
        {%- if uml_params.states[state].exit is not none %}
{{uml_params.states[state].exit|indent(indentation_level,true)}}
        {%- endif %}
        {%- if uml_params.states[transition.destination].entry is not none %}
{{uml_params.states[transition.destination].entry|indent(indentation_level,true)}}
        {%- endif %}
        {%- if uml_params.states[transition.destination].submachine != [] %}
        {%- for submachine in uml_params.states[transition.destination].submachine %}
{{(submachine.title + '_initialize();')|indent(indentation_level,true)}}
        {%- endfor %}
        {%- endif %}
{{(fsm_name + '_state = ' + 'STATE_' + fsm_name.upper() + '_' + transition.destination.upper())|indent(indentation_level,true)}};
{{ (delay_name + ' = 0')|indent(indentation_level,true)}};
{{('printf("Transition from: ' + state.upper() +' to: ' + transition.destination.upper() +' \\r\\n");')|indent(indentation_level,true)}}
    {%- if transition.conditions is not none %}
    }
    {%- endif %}
    {%- endfor %}
}
{% endfor %}
{%- endmacro %}

{#- Main FSM #}

/******** {{fsm_name}} ********/
t_states_{{fsm_name}} {{fsm_name}}_get_state( void )
{
    return {{fsm_name}}_state;
}

{{core_code_implementation(fsm_name, uml_params, 'delay')}}


/*** State implementations for {{fsm_name}} ***/
{{function_implementation(fsm_name, uml_params, 'delay')}}


{% for submachine in submachines_list %}
/******** {{submachine.title}} ********/
t_states_{{submachine.title}} {{submachine.title}}_get_state( void )
{
    return {{submachine.title}}_state;
}

{{core_code_implementation(submachine.title, submachine,'delay_' + submachine.title.lower().replace('_submachine',''), false )}}


/*** State implementations for {{submachine.title}} ***/
{{function_implementation(submachine.title, submachine,'delay_' + submachine.title.lower().replace('_submachine','') )}}
{%- endfor %}
