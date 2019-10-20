/**
 * @file {{file_name}}
{% for n in uml %} * {{n}}{% endfor %} *
 **/
{% set fsm_name = file_name.replace('.h','') %}

/* States of main FSM */
typedef enum{
{%- for state in uml_params.states %}
{%- if state == '[*]' %}
    STATE_INITIAL,
{%- else %}
    STATE_{{state.upper()}},
{%- endif %}
{%- endfor %}
} t_states_{{fsm_name}};

void {{fsm_name}}_initialize( void );

void {{fsm_name}}_task( void );
