import pandas as pd
import numpy as np

# Timing
effective_month = 1  # leave as is
drill_month = 1
completion_month = 2
first_prod_month = 3
days_in_month = 30

# Oil Type Curve Parameters
qi_oil = 490  # 24-hr IP, Bblspd
b_oil = 0.90
# De_oil = 0.7575
Di_oil = 0.943
# Dmin_oil = 0.06
time_period = 360  # months

# Nat Gas Type Curve Parameters
qi_gas = 975  # 24-hr IP, Mcfpd
b_gas = 0.95
# De_gas = 0.40
Di_gas = 0.48
# Dmin_gas = 0.06
shrink = 0.26
NGL_MMcf = 67  # Bbls/MMcf
btu_factor_recovered_gas = 1.03

# Water Type Curve Parameters
qi_water = 1200  # 24-hr IP, Mcfpd
b_water = 1.001
# De_water = 0.62
Di_water = 0.805
# Dmin_water = 0.06
# water_to_oil = 3.0  # Bbls/Bbls

# Price Deck Assumptions
oil_price_deck = 80.00
oil_basis = -1.80
realized_oil_price_deck = oil_price_deck + oil_basis
gas_price_deck = 2.25
gas_basis = -0.280
realized_gas_price_deck = ((gas_price_deck + gas_basis) * btu_factor_recovered_gas)
ngl_price_relative_to_oil = 0.50
realized_ngl_price_deck = oil_price_deck * ngl_price_relative_to_oil

# Ownership Assumptions
wi = 1.00  # (e.g., 1.00 = 100%, 0.50 = 50%)
royalties = 0.16
nri = wi * (1 - royalties)

# Opex, D&C, Tax, and PV Assumptions
fixed_loe_period_1_cost = 9.5  # $000s
fixed_loe_period_1_begin = first_prod_month
fixed_loe_period_1_duration = 18  # months
fixed_loe_period_1_end = first_prod_month + fixed_loe_period_1_duration - 1
fixed_loe_period_2_cost = 8.0  # $000s
fixed_loe_period_2_begin = fixed_loe_period_1_end + 1
fixed_loe_period_2_duration = 12  # months
fixed_loe_period_2_end = fixed_loe_period_2_begin + fixed_loe_period_2_duration - 1
fixed_loe_period_3_cost = 7.7  # $000s
fixed_loe_period_3_begin = fixed_loe_period_2_end + 1
fixed_loe_period_3_duration = 30  # months
fixed_loe_period_3_end = fixed_loe_period_3_begin + fixed_loe_period_3_duration - 1
fixed_loe_period_4_cost = 4.0  # $000s
fixed_loe_period_4_begin = fixed_loe_period_3_end + 1
variable_loe_oil = 0.80  # $/Bbl
variable_loe_gas = 0.00  # $/Mcf
variable_loe_water = 1.46  # #/Bow
gcp = 0.92  # $/NRI Mcf
drilling_capex = 1600  # $000s
completion_capex = 2200  # $000s
ad_val_tax = 0.00  # % of revenues
prod_tax = 0.072  # % of revenues
disc_rate = 0.20  # %

# Gross Production Calculations (Hyperbolic Decline)
period = range(1, time_period + 1)
gross_oil_prod_forecast = {t: float(((qi_oil / ((1 + (b_oil * Di_oil * t)) ** (1 / b_oil))) * days_in_month) / 1000) for
                           t in range(time_period)}
gross_gas_prod_forecast = {t: float(((qi_gas / ((1 + (b_gas * Di_gas * t)) ** (1 / b_gas))) * days_in_month) / 1000) for
                           t in range(time_period)}
gross_ngl_prod_forecast = {t: ((gross_gas_prod_forecast[t] * NGL_MMcf) / 1000) for t in range(time_period)}
gross_water_prod_forecast = {t: float(((qi_water / ((1 + (b_water * Di_water * t)) ** (1 / b_water))) * days_in_month)
                            / 1000) for t in range(time_period)}
# gross_water_prod_forecast = {t: (gross_oil_prod_forecast[t] * water_to_oil) for t in
#                              range(time_period)}

# Build Data Frame
df = pd.DataFrame.from_dict({'period': pd.Series(period),
                             'gross_oil_prod': pd.Series(gross_oil_prod_forecast),
                             'gross_gas_prod': pd.Series(gross_gas_prod_forecast),
                             'gross_ngl_prod': pd.Series(gross_ngl_prod_forecast),
                             'gross_water_prod': pd.Series(gross_water_prod_forecast)})

# df = pd.read_csv('production_forecast.csv')
# df['gross_ngl_prod'] = ((df.gross_gas_prod * NGL_MMcf) / 1000)

# Shift forecasts down to start at first production month
df['gross_oil_prod'] = df['gross_oil_prod'].shift(first_prod_month - 1, fill_value=0)
df['gross_gas_prod'] = df['gross_gas_prod'].shift(first_prod_month - 1, fill_value=0)
df['gross_ngl_prod'] = df['gross_ngl_prod'].shift(first_prod_month - 1, fill_value=0)
df['gross_water_prod'] = df['gross_water_prod'].shift(first_prod_month - 1, fill_value=0)

# WI Production Calculations
df['wi_oil_prod'] = df.gross_oil_prod * wi
df['wi_gas_prod'] = df.gross_gas_prod * (1 - shrink) * wi
df['wi_ngl_prod'] = df.gross_ngl_prod * wi
df['wi_water_prod'] = df.gross_water_prod * wi

# NRI Production Calculations
df['net_oil_prod'] = df.gross_oil_prod * nri
df['net_gas_prod'] = df.gross_gas_prod * (1 - shrink) * nri
df['net_ngl_prod'] = df.gross_ngl_prod * nri

# Price Forecasts
df['realized_oil_price'] = realized_oil_price_deck
df['realized_gas_price'] = realized_gas_price_deck
df['realized_ngl_price'] = realized_ngl_price_deck

# Revenue Calculations
df['oil_revenue'] = df.net_oil_prod * df.realized_oil_price
df['gas_revenue'] = df.net_gas_prod * df.realized_gas_price
df['ngl_revenue'] = df.net_ngl_prod * df.realized_ngl_price
df['total_revenue'] = df.oil_revenue + df.gas_revenue + df.ngl_revenue

# Opex Calculations
df['fixed_loe'] = np.where(df.period.between(fixed_loe_period_1_begin, fixed_loe_period_1_end, inclusive='both'),
                           fixed_loe_period_1_cost * wi,
                           np.where(
                               df.period.between(fixed_loe_period_2_begin, fixed_loe_period_2_end, inclusive='both'),
                               fixed_loe_period_2_cost * wi,
                               np.where(df.period.between(fixed_loe_period_3_begin, fixed_loe_period_3_end,
                                                          inclusive='both'), fixed_loe_period_3_cost * wi,
                                        np.where(df.period >= fixed_loe_period_4_begin,
                                                 fixed_loe_period_4_cost * wi, 0))))

df['variable_loe_oil'] = df.wi_oil_prod * variable_loe_oil
df['variable_loe_gas'] = df.wi_oil_prod * variable_loe_gas
df['variable_loe_water'] = df.wi_water_prod * variable_loe_water
df['total_variable_loe'] = df.variable_loe_oil + df.variable_loe_gas + df.variable_loe_water
df['gcp'] = df.net_gas_prod * gcp
df['prod_tax'] = df.total_revenue * prod_tax
df['ad_val_tax'] = df.total_revenue * ad_val_tax
df['total_expenses'] = df.fixed_loe + df.total_variable_loe + df.gcp + df.prod_tax + df.ad_val_tax

# D&C Calculations
df['drilling_capex'] = np.where(df.period == drill_month, drilling_capex * wi, 0)
df['completion_capex'] = np.where(df.period == completion_month, completion_capex * wi, 0)
df['d_and_c'] = df.drilling_capex + df.completion_capex

# Net Cash Flow and PV Calculations
df['undisc_cf'] = df.total_revenue - df.total_expenses - df.d_and_c
# df = df.drop(df.index[df.undisc_cf < 0])  # eliminates all rows once undiscounted cash flows go negative
df = df.drop(df.index[(df.undisc_cf < 0) & (df.period > completion_month)])
df.loc['total'] = df.iloc[:, 1:].sum()
# df.loc['total', 'period'] = ''  # gets rid of 'nan' that gets print by the code in the row immediately above
df['PV-{:.1%}'.format(disc_rate)] = df.undisc_cf / ((1 + disc_rate / 12) ** df.period)
df['Cum PV-{:.1%}'.format(disc_rate)] = df['PV-{:.1%}'.format(disc_rate)].cumsum(axis=0)

# Formatting
pd.options.display.float_format = '{:,.2f}'.format
columns_to_drop = ['wi_oil_prod', 'wi_gas_prod', 'wi_ngl_prod', 'wi_water_prod', 'drilling_capex', 'completion_capex',
                   'PV-{:.1%}'.format(disc_rate)]
# 'variable_loe_oil', 'variable_loe_gas', 'variable_loe_water'
df = df.drop(columns=columns_to_drop)
pd.set_option('display.max_rows', 999)
pd.set_option('display.max_columns', 999)
# print(df.head(30))
print(df)
# print(df.dtypes)
df.to_csv('output.csv')
# df.to_excel('output.xlsx')
