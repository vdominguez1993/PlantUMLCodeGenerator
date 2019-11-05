/**
 * @file {{file_name}}
{% for n in uml %} * {{n}}{% endfor %} *
 **/
{% set fsm_name = file_name.replace('.h','') %}
{%- set submachines_list = get_submachines(uml_params) %}

#ifndef _{{fsm_name.upper()}}_
#define _{{fsm_name.upper()}}_

/* States of main FSM */
typedef enum{
{%- for state in uml_params.states %}
{%- if state == '[*]' %}
    STATE_{{fsm_name.upper()}}_INITIAL,
{%- else %}
    STATE_{{fsm_name.upper()}}_{{state.upper()}},
{%- endif %}
{%- endfor %}
} t_states_{{fsm_name}};

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

void {{fsm_name}}_initialize( void );

void {{fsm_name}}_task( void );

t_states_{{fsm_name}} {{fsm_name}}_get_state( void );

{%- for submachine in submachines_list %}
t_states_{{submachine.title}} {{submachine.title}}_get_state( void );
{%- endfor %}

#endif
