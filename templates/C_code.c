/**
 * @file {{file_name}}
{% for n in uml %} * {{n}}{% endfor %} *
 **/
{#- Jinja function calls and variables #}
{%- set fsm_name = file_name.replace('.c','') %}
{%- set submachines_list = get_submachines(uml_params) %}


#include "{{file_name.replace('.c','.h')}}"

/* Typedefs */
/* States of submachines */
{%- for submachine in submachines_list %}
typedef enum{
{%- for state in submachine.states %}
{%- if state == '[*]' %}
    STATE_{{submachine.title.upper()}}_INITIAL,
{%- else %}
    STATE_{{submachine.title.upper()}}_{{state.upper()}},
{%- endif %}
{%- endfor %}
} t_states_{{submachine.title}};
{%- endfor %}

static t_{{fsm_name}} {{fsm_name}}_state = STATE_INITIAL;
{% for submachine in submachines_list %}
static t_{{submachine.title}} {{submachine.title}}_state = STATE_{{submachine.title.upper()}}_INITIAL;
{%- endfor %}

{# Submachine function prototypes #}
{% for submachine in submachines_list %}
/*** Submachine prototypes for task and init ***/
static void {{submachine.title + '_init'}}( void );

static void {{submachine.title + '_task'}}( void );
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

{%- macro core_code_implementation(fsm_name, uml_params) %}
void {{fsm_name}}_initialize( void ){
    static t_{{fsm_name}} {{fsm_name}}_state = STATE_INITIAL;
}

void {{fsm_name}}_task( void ){
    switch ({{fsm_name}}_state){
{%- for state in uml_params.states %}
    {#- Exception for initial state #}
    {%- if state == '[*]' %}
        case STATE_INITIAL:
            initial_state();
    {%- else %}
        case STATE_{{state.upper()}}:
            {{state.lower()}}();
    {%- endif %}
            break;
{%- endfor %}
        default:
            {{fsm_name}}_state = STATE_INITIAL;
            break;
    }
}
{%- endmacro %}

{%- macro function_implementation(fsm_name, uml_params) %}
{%- for state in uml_params.states %}
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
        {%- if uml_params.states[state].exit is not none %}
{{uml_params.states[state].exit|indent(indentation_level,true)}}
        {%- endif %}
        {%- if uml_params.states[transition.destination].entry is not none %}
{{uml_params.states[transition.destination].entry|indent(indentation_level,true)}}
        {%- endif %}
        {%- if uml_params.states[transition.destination].submachine != [] %}
        {%- for submachine in uml_params.states[transition.destination].submachine %}
{{(submachine.title + '_init();')|indent(indentation_level,true)}}
        {%- endfor %}
        {%- endif %}
{{('state = ' + transition.destination.upper())|indent(indentation_level,true)}};
    {%- if transition.conditions is not none %}
    }
    {%- endif %}
    {%- endfor %}
}
{%- endfor %}
{%- endmacro %}

{#- Main FSM #}

/******** {{fsm_name}} ********/
{{core_code_implementation(fsm_name, uml_params)}}


/*** State implementations for {{fsm_name}} ***/
{{function_implementation(fsm_name, uml_params)}}


{% for submachine in submachines_list %}
/******** {{submachine.title}} ********/
{{core_code_implementation(submachine.title, submachine)}}


/*** State implementations for {{submachine.title}} ***/
{{function_implementation(submachine.title, submachine)}}
{%- endfor %}
