import dash
from dash import Dash, html, Output, Input, dcc, callback
import dash_bootstrap_components as dbc
from dash_bootstrap_components import themes
import plotly.express as px
import pandas as pd
import json
import collections
import numpy as np
from io import BytesIO


with open("/home/alber/PycharmProjects/tfg/spain-provinces.geojson") as file:
	provinces = json.load(file)


def make_map_df(var, df):
	listProvinces = []
	# print(len(provinces['features']))
	for i in range(0, len(provinces['features'])):
		listProvinces.append(provinces['features'][i]['properties']['name'])

	# print(listProvinces)
	list1 = []
	for i in range(len(df)):
		list1.append(df.loc[i, 'region'])

	print(list1)
	c = collections.Counter(list1)
	print(c)
	regions = []
	for region in c.keys():
		regions.append(str(region).capitalize())
	print(regions)
	executions = []
	emissions = []
	for prov in listProvinces:
		if '/' in prov:
			parts = prov.split('/')
			prov = parts[1]
		if var == 'executions':
			if prov not in regions:
				executions.append(0)
			else:
				executions.append(int(c[prov.lower()]))
		else:
			totalemissions = 0
			if prov not in regions:
				emissions.append(0)
			else:
				for i in range(len(df)):
					if df.loc[i, 'region'] == prov.lower():
						totalemissions = totalemissions + float(df.loc[i, 'emissions'])

				emissions.append(totalemissions)
	# print(executions)
	df2 = pd.DataFrame()
	df2['region'] = listProvinces
	if var == 'emissions':
		df2['emissions'] = emissions
	else:
		df2['executions'] = executions
	# print(emissions)
	# print(df2.to_string())
	return df2


def make_choropleth(var, df):
	dfMap = make_map_df(var, df)
	# print(dfMap)
	column = ''
	scale = ''
	# print('choropleth: ' + var)
	if var == 'emissions':
		column = 'emissions'
		scale = 'YlOrRd'
	else:
		column = 'executions'
		scale = 'blues'

	return px.choropleth_mapbox(dfMap, geojson=provinces,
								featureidkey='properties.name',
								locations='region',
								color=column,
								color_continuous_scale=scale,
								mapbox_style='open-street-map',
								center=dict(lat=40.0, lon=-3.72),
								zoom=4)


def approximate_numbers(number):
	number = str(number)
	if 'e' in number:
		value = float(number)
		return np.format_float_scientific(value, precision=4, exp_digits=3)
	else:
		if '.' in number:
			return str(round(float(number), 4))
		else:
			return str(number)


def serve_layout():
	return dbc.Container([
		dbc.Row([
			dbc.Col(html.H1('Emissions Dashboard', className='text-center text-success mb-4'))
		]),
		html.Hr(),
		dbc.Row([
			dbc.Tabs(id='tabs', active_tab='CPU', children=[
				dbc.Tab(label='CPU', tab_id='CPU', labelClassName='text-success'),
				dbc.Tab(label='GPU', tab_id='GPU', labelClassName='text-success'),
				dbc.Tab(label='RAM', tab_id='RAM', labelClassName='text-success'),
				dbc.Tab(label='Summary', tab_id='Summary', labelClassName='text-success'),
			],),
		]),
		html.Button(id='to-load-df', style={'display': 'none'}),
		dcc.Store(id='load-df'),
		dbc.Row(id='tabs-content', children=[]),
		html.Hr(),
		dbc.Row([
			dbc.Tabs(id='tabs2', active_tab='CO2 total emissions', children=[
				dbc.Tab(label='CO2 total emissions', tab_id='CO2 total emissions', labelClassName='text-success'),
				dbc.Tab(label='Num. executions', tab_id='Num. executions', labelClassName='text-success'),
			],),
		]),
		dbc.Row([
			dbc.Col(dcc.Graph(id='control-map', figure={}, className="mb-4"), width=8),
			dbc.Col([
				dbc.Stack([
					html.H5('SELECT A REGION ON THE MAP TO SEE MORE DETAILS OF THE LAST EXECUTION ON EACH REGION'),
					dbc.Card(id='control-info'),
				])
			]),])
		], fluid=True)



graphs_labels = {
			'cpu_power': 'CPU POWER (W)',
			'cpu_energy': 'CPU ENERGY (kWh)',
			'gpu_power': 'GPU POWER (W)',
			'gpu_energy': 'GPU ENERGY (kWh)',
			'ram_power': 'RAM POWER (W)',
			'ram_energy': 'RAM ENERGY (kWh)',
			'timestamp': 'Date'
		}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],
				meta_tags=[{'name': 'viewport',
				'content': 'width=device-width, initial-scale=1.0'}]) #para layout responsive
				# https://www.youtube.com/watch?v=0mfIK8zxUds&list=PLh3I780jNsiS3xlk-eLU2dpW3U-wCq4LW&index=1&t=1886s&ab_channel=CharmingData
				# https://dash-bootstrap-components.opensource.faculty.ai/docs/faq/




app.layout = serve_layout


@callback(
	Output('load-df', 'data'),
	Input('to-load-df', 'n_clicks')
)
def clean_data(n_clicks):
	print("cargo dataset")
	df = pd.read_csv('/home/alber/PycharmProjects/tfg/emissions.csv')
	return df.to_json()


@callback(
	Output(component_id='control-map', component_property='figure'),
	Input(component_id='tabs2', component_property='active_tab'),
	Input(component_id='load-df', component_property='data')
)
def update_map(active_tab, json_data):
	bytes_data = json_data.encode('utf-8')
	df = pd.read_json(BytesIO(bytes_data))
	if active_tab == 'CO2 total emissions':
		var = 'emissions'
	else:
		var = 'executions'
	fig = make_choropleth(var, df)
	return fig


@callback(
	Output(component_id='control-info', component_property='children'),
	Input(component_id='control-map', component_property='clickData'),
	Input(component_id='load-df', component_property='data')
)
def update_info(clickData, json_data):
	if clickData is not None:
		bytes_data = json_data.encode('utf-8')
		df = pd.read_json(BytesIO(bytes_data))
		print(clickData)
		location = clickData['points'][0]['location']
		print('location', location)

		'''
		list = df.loc[df['region'] == location.lower()]

		for i in list:
			print(i['timestamp'])
		print(list)
		timestamp = list['timestamp']
		print(timestamp)
		'''
		for i in range(len(df)-1, -1, -1):
			prov = location.lower()
			if '/' in prov:
				parts = prov.split('/')
				prov = parts[1]
			if df.loc[i, 'region'] == prov:
				return [html.H4('Metadata of last execution in {}:'.format(location)),
						   html.H6('Project name: {}'.format(df.loc[i, 'project_name'])),
						   html.H6('O.S.: {}'.format(df.loc[i, 'os'])),
						   html.H6('Python version: {}'.format(df.loc[i, 'python_version'])),
						   html.H6('CPU model: {}'.format(df.loc[i, 'cpu_model'])),
						   html.H6('CPU count: {}'.format(df.loc[i, 'cpu_count'])),
						   html.H6('GPU model: {}'.format(df.loc[i, 'gpu_model'])),
						   html.H6('RAM size: {} Gb'.format(df.loc[i, 'ram_total_size'])),
						   html.H6('CPU model: {}'.format(df.loc[i, 'cpu_model'])),
						   html.H6('Emissions: {} kg'.format(df.loc[i, 'emissions']))]

		return [html.H4('No executions in {}'.format(location))]


@callback(
	Output(component_id='tabs-content', component_property='children'),
	Input(component_id='tabs', component_property='active_tab'),
	Input(component_id='load-df', component_property='data')
)
def update_content_from_tabs(active_tab, json_data):
	bytes_data = json_data.encode('utf-8')
	df = pd.read_json(BytesIO(bytes_data))

	if active_tab == 'Summary':
		power_used = approximate_numbers(df['cpu_power'].sum() + df['gpu_power'].sum() + df['ram_power'].sum())
		energy_used = approximate_numbers(df['energy_consumed'].sum())
		print('AMM ' + str(df['energy_consumed'].sum()))
		print('AMM ' + energy_used)
		total_emissions = approximate_numbers(df['emissions'].sum())
		return [dbc.Col([dbc.Card(
				dbc.CardBody([
					html.H3('Total POWER used: '.format(active_tab)),
					html.H4(power_used + ' W'),
				])
			),], style={'margin-top': '12px'}),
			dbc.Col([dbc.Card(
				dbc.CardBody([
					html.H3('Total ENERGY used: '.format(active_tab)),
					html.H4(energy_used + ' kWh'),
				])
			), ],style={'margin-top': '12px'}),
			dbc.Col([dbc.Card(
				dbc.CardBody([
					html.H3('Total emissions generated: '),
					html.H4(total_emissions + ' Kg. eq. CO2'),
				])
			), ], style={'margin-top': '12px'}),
		]
	else:
		average_power = approximate_numbers(df['{}_power'.format(active_tab.lower())].mean())
		average_energy = approximate_numbers(df['{}_energy'.format(active_tab.lower())].mean())
		return [dbc.Col([
				html.H5('{} power (W) by date'.format(active_tab), className='text-center'),
				dcc.Graph(figure=px.line(df, x='timestamp', y='{}_power'.format(active_tab.lower()), markers=True, labels=graphs_labels), id='cpu_power', className='mb-2'),
			]),
			dbc.Col([
				html.H5('Energy used per {} (kWh) by date'.format(active_tab), className='text-center'),
				dcc.Graph(figure=px.line(df, x='timestamp', y='{}_energy'.format(active_tab.lower()), markers=True, labels=graphs_labels), id='cpu_energy', className='mb-2')
			]),
			dbc.Col([
				dbc.Stack([
					dbc.Card(
						dbc.CardBody([
							html.H3('Average {} POWER used: '.format(active_tab)),
							html.H4(average_power + ' W'),
						]),
					),
					dbc.Card(
						dbc.CardBody([
							html.H3('Average {} ENERGY used: '.format(active_tab)),
							html.H4(average_energy + ' kWh')
						]),
					),
				], gap=3)

			], className="align-self-center")]


if __name__ == '__main__':
	app.run_server(debug=True)
