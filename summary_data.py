import altair as alt
import dabest
from funcs import (read_summary_data, read_config_file, clean_config_file, clean_summary_data, merge_config_file,
                   add_featuers, rename_columns)
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go

import yaml
import pandas as pd

file_path = '/Users/orikobi/PycharmProjects/uni/reaserch/config.yaml'

with open(file_path, 'r') as file:
    yaml_data = yaml.safe_load(file)

cols_to_read = yaml_data['cols_to_read']
cols_mapping = yaml_data['cols_mapping']
path_to_write = yaml_data['path_to_write']
basic_path = yaml_data['basic_path']


config = read_config_file(f'{basic_path}/fact_table.csv')
exp_with_fam = config.groupby(['subject_id']).agg(expiriance=('date', 'nunique')).reset_index()
config = clean_config_file(config)

HR_DATA = pd.read_csv(f'/Users/orikobi/Downloads/data.csv', usecols=['subject_id', 'set', 'day', 'HR'])
summary = read_summary_data(f'{basic_path}/summary_data/', cols_to_read)
summary = clean_summary_data(summary)

merged = merge_config_file(summary, config)
merged = rename_columns(merged, cols_mapping)
merged = add_featuers(merged, exp_with_fam)
merged = merged.sort_values(by=['day', 'set', 'rpe'])
merged['rpe'] = merged['rpe'].astype(str)
merged = pd.merge(merged, HR_DATA, on=['subject_id', 'set', 'day'], how='left')

gdf = merged.melt(id_vars=['rpe'], value_vars=['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7'], var_name='speed_zones')

# Define the order of the speed_zones
speed_zones_order = ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7']
gdf['speed_zones'] = pd.Categorical(gdf['speed_zones'], categories=speed_zones_order, ordered=True)

# Group by and calculate the mean
gdf = gdf.groupby(['rpe', 'speed_zones'])['value'].mean().reset_index()
gdf = gdf.sort_values(by=['rpe', 'speed_zones'])



rpe_order = ['6', '8', '10']  # Define the order of the rpe facet column

fig = px.pie(gdf, values='value', names='speed_zones', facet_col='rpe',labels='RPE', category_orders={'speed_zones': speed_zones_order, 'rpe': rpe_order},)

# Update the traces
fig.update_traces(
    textinfo='percent+value',
    texttemplate='%{percent:.1%} (%{value:.0f})',
    textposition='inside'
)

fig.update_layout(
    uniformtext_minsize=10, uniformtext_mode='hide',
    legend=dict(font=dict(size=12)),
    margin=dict(
        l=0, r=0, b=0, t=50, pad=0,
    font=dict(
        family="Courier New, monospace",
        size=18,  # Set the font size here
        color="RebeccaPurple"
    )
))

fig.show()





merged.to_csv(f'{basic_path}/summary_data.csv', index=False)


color_scale = alt.Scale(domain=merged['color'].unique().tolist(),
                        range=merged['color'].unique().tolist())

label_font_size = 14
parameter = 'Intense Acc_Decl actions'
parameter1 = 'Sprint Count (#)'
parameter2 = 'Distance Covered (m)'

selection = alt.selection_single(fields=['name'], empty=True)

dabest_df = merged.groupby(['subject_id', 'rpe', 'name']).agg({parameter: 'mean', parameter1: 'mean', parameter2:'mean'}).reset_index()

dabest_df['rpe'] = dabest_df['rpe'].astype(str)



df_1 = dabest.load(data=dabest_df, x="rpe", y=parameter, idx=('6', '8', '10'), paired="baseline",
                        id_col="subject_id")
df_1.mean_diff.plot(fig_size=(12, 10)).savefig('plot1.png')


df_2 = dabest.load(data=dabest_df, x="rpe", y=parameter1, idx=('6', '8', '10'), paired="baseline",
                        id_col="subject_id")
df_2.mean_diff.plot(fig_size=(12, 10)).savefig('plot2.png')


df_3 = dabest.load(data=dabest_df, x="rpe", y=parameter2, idx=('6', '8', '10'), paired="baseline",
                        id_col="subject_id")
df_3.mean_diff.plot(fig_size=(12, 10)).savefig('plot3.png')



subject_selection = alt.selection_multi(fields=['subject_id'], empty='all', name='Subject')

# Create Altair Chart
exp_chart = alt.Chart(merged).mark_line(point=True).encode(
    x='rpe:N',
    y=alt.Y(parameter, title=parameter),
    color=alt.Color('subject_id:N', legend=alt.Legend(title='Subject ID'), scale=alt.Scale(scheme='category10')),
    facet=alt.Facet('experience:N', columns=4),
    opacity=alt.condition(subject_selection, alt.value(1), alt.value(0.1))
).properties(
    title=alt.TitleParams('To be decided', color='black'),
    width=400,  # Adjust width as needed
    height=250  # Adjust height as needed
).add_selection(
    subject_selection
).transform_filter(
    subject_selection
)

# Bind legend selection to the main selection
exp_chart = exp_chart.add_selection(
    alt.selection_multi(fields=['subject_id'], bind='legend', name='Subject')
)

# Allow clicking on empty area of the chart to reset selection
exp_chart = exp_chart.add_selection(
    alt.selection_multi(on='mouseover', empty='all', name='Reset')
)



day_2_df = merged[merged['day'] == 2]

chart2 = alt.Chart(day_2_df).mark_bar().encode(
    x=alt.X('name', axis=alt.Axis(grid=False, title=None, labelAngle=45, labelFontSize=label_font_size, labelColor='white')),
    y=alt.Y(parameter, axis=alt.Axis(grid=False, title=parameter, titleColor='white', labelColor='white')),
    color=alt.condition(selection,
                        alt.Color('color:N', scale=color_scale),
                        alt.value('gray')),
    facet=alt.Facet('facet_combined:N', columns=3, header=alt.Header(labelColor='white')),
    tooltip=[parameter, 'name', 'color']
).properties(
    title=alt.TitleParams('######### Day 2 ###########', color='white')
).add_selection(selection).configure(background='black')

day_3_df = merged[merged['day'] == 3]

chart3 = alt.Chart(day_3_df).mark_bar().encode(
    x=alt.X('name', axis=alt.Axis(grid=False, title=None, labelAngle=45, labelFontSize=label_font_size, labelColor='white')),
    y=alt.Y(parameter, axis=alt.Axis(grid=False, title=parameter, titleColor='white', labelColor='white')),
    color=alt.condition(selection,
                        alt.Color('color:N', scale=color_scale),
                        alt.value('gray')),
    facet=alt.Facet('facet_combined:N', columns=3, header=alt.Header(labelColor='white')),
    tooltip=[parameter, 'name', 'color']
).properties(
    title=alt.TitleParams('######### Day 3 ###########', color='white')
).add_selection(selection).configure(background='black')

day_4_df = merged[merged['day'] == 4]

chart4 = alt.Chart(day_4_df).mark_bar().encode(
    x=alt.X('name', axis=alt.Axis(grid=False, title=None, labelAngle=45, labelFontSize=label_font_size, labelColor='white')),
    y=alt.Y(parameter, axis=alt.Axis(grid=False, title=parameter, titleColor='white', labelColor='white')),
    color=alt.condition(selection,
                        alt.Color('color:N', scale=color_scale),
                        alt.value('gray')),
    facet=alt.Facet('facet_combined:N', columns=3, header=alt.Header(labelColor='white')),
    tooltip=[parameter, 'name', 'color']
).properties(
    title=alt.TitleParams('######### Day 4 ###########', color='white')
).add_selection(selection).configure(background='black')

with open('htmls/template_summary.html', 'r') as f:
    html_template = f.read()

    # Replace placeholders with actual values
html_content = html_template.format(
    vega_version=alt.VEGA_VERSION,
    vegalite_version=alt.VEGALITE_VERSION,
    vegaembed_version=alt.VEGAEMBED_VERSION,
    image1='<img src="plot1.png" alt="Plot">',
    image2='<img src="plot2.png" alt="Plot">',
    image3='<img src="plot3.png" alt="Plot">',
    spec1=exp_chart.to_json(indent=None),
    spec2=chart2.to_json(indent=None),
    spec3=chart3.to_json(indent=None),
    spec4=chart4.to_json(indent=None),
)

# Write HTML content to file
with open(f'master_dashboard.html', 'w') as f:
    f.write(html_content)















