/**
 * @file {{file_name}}
{% for n in uml %} * {{n}}{% endfor %} *
 **/
{%- set fsm_name = file_name.replace('.c','') %}

#include "{{file_name.replace('.c','.h')}}"

static t_{{fsm_name}} {{fsm_name}}_state = STATE_INITIAL;

{% for state in uml_params.states %}
{%- if state == '[*]' %}
static void initial_state( void );
{%- else %}
static void {{state.lower()}}( void );
{%- endif %}
{% endfor %}


{# Core code #}
void {{fsm_name}}_initialize( void ){
    static t_{{fsm_name}} {{fsm_name}}_state = STATE_INITIAL;
}

void {{fsm_name}}_task( void ){
    switch ({{fsm_name}}_state){
{%- for state in uml_params.states %}
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


{# State Code #}
{% for state in uml_params.states %}
{%- if state == '[*]' %}
static void initial_state( void ){
{%- else %}
static void {{state.lower()}}( void ){
{%- endif %}

    {%- for transition in uml_params.states[state].transitions %}
    {%- if transition.conditions is not none %}
    if ({{transition.conditions}}) {
        state = {{transition.destination.upper()}};
    }
    {%- else %}
    state = {{transition.destination.upper()}};
    {%- endif %}
    {%- endfor %}
}
{% endfor %}
