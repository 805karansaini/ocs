import copy
import datetime
import math
from collections import defaultdict

import scipy.stats

from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class CalcluateGreeks:
    def compute_all_greeks(combination, list_of_config_leg_object):

        # Default dict with value as 0
        net_greeks = defaultdict(float)

        # Loop over the leg tuple of each combination
        for leg_tuple, config_leg_object in zip(combination, list_of_config_leg_object):
            
            # Mulitplier
            # InstrumentID, and InstrumentObject for multiplier
            instrument_id = config_leg_object.instrument_id
            if instrument_id not in StrategyVariables.map_instrument_id_to_instrument_object:
                multiplier = 100
                print("compute_all_greeks: Not Found", multiplier)
            else:
                multiplier = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id].multiplier)
                print("compute_all_greeks: Found", multiplier)

            # print(f"Leg Tuple: {leg_tuple}")

            # Unpack the values stored in tuple
            _, strike, _, _, expiry, bid, ask, _, _, vega, theta, gamma, underlying_price = leg_tuple
            options_prem = (bid + ask) / 2
            quantity = config_leg_object.quantity

            # Calcluate the time to expiration for the greeks
            current_date = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj = datetime.datetime.strptime(current_date, "%Y%m%d")

            expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
            time_to_expiration = abs(current_date_obj - expiry_date_obj).days

            # Handling the case when 'time_to_expiration' is 0
            if time_to_expiration == 0:
                time_to_expiration = 1
            time_to_expiration = (time_to_expiration) / 365

            # Get the IV for the greeks calcluation
            sigma = Utils.get_implied_volatility(
                float(underlying_price),
                StrategyVariables.riskfree_rate1,
                0,
                time_to_expiration,
                strike,
                options_prem,
                config_leg_object.right,
            )

            # Calcluate Vanna greeks for each leg_tuple
            vanna = CalcluateGreeks.calculate_vanna(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0
            )

            # Calcluate Zomma greeks for each leg_tuple
            zomma = CalcluateGreeks.calculate_zomma(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0
            )

            # Calcluate Vomma greeks for each leg_tuple
            vomma = CalcluateGreeks.calculate_vomma(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0
            )

            # Calcluate Charm greeks for each leg_tuple
            charm = CalcluateGreeks.calculate_charm(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0, config_leg_object.right
            )

            # Calcluate speed greeks for each leg_tuple
            speed = CalcluateGreeks.calculate_speed(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0
            )

            # Calcluate color greeks for each leg_tuple
            color = CalcluateGreeks.calculate_color(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0
            )

            # Calcluate veta greeks for each leg_tuple
            veta = CalcluateGreeks.calculate_veta(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0
            )

            # Calcluate ultima greeks for each leg_tuple
            ultima = CalcluateGreeks.calculate_ultima(
                float(underlying_price), strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0
            )

            # Store the greeks in dictionary for each leg tuple
            greeks_dict = {
                "vanna": vanna,
                "zomma": zomma,
                "vomma": vomma,
                "charm": charm,
                "speed": speed,
                "color": color,
                "veta": veta,
                "ultima": ultima,
                "vega": vega,
                "theta": theta,
                "gamma": gamma,
            }
            for greek, value in greeks_dict.items():
                if config_leg_object.action.upper() == "BUY":
                    net_greeks[greek] += float(value) * quantity * multiplier
                elif config_leg_object.action.upper() == "SELL":
                    net_greeks[greek] -= float(value) * quantity * multiplier

        return net_greeks

    @staticmethod
    def calculate_vanna(S, X, t, r1, sigma, q):
        # Calculate d1 and d2
        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S / X) + (r1 - q + 0.5 * sigma**2) * t) / sigma_t
        d2 = d1 - sigma_t

        # Calculate Vanna
        vanna_num = -math.exp(-q * t) * scipy.stats.norm.pdf(d1) * d2
        vanna_deno = sigma
        vanna = vanna_num / vanna_deno

        return vanna

    @staticmethod
    def calculate_zomma(S, X, t, r1, sigma, q):
        # Calculate d1 and d2
        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S / X) + (r1 - q + 0.5 * sigma**2) * t) / sigma_t
        d2 = d1 - sigma_t

        # Calculate Zomma
        # zomma = (math.exp(-q * t) * scipy.stats.norm.pdf(d1)) / (S * sigma**2 * math.sqrt(t)) * (d1 * d2 - 1)
        zomma_num = math.exp(-q * t) * scipy.stats.norm.pdf(d1) * (d1 * d2 - 1)
        zomma_deno = S * sigma**2 * math.sqrt(t)
        zomma = zomma_num / zomma_deno

        return zomma

    @staticmethod
    def calculate_vomma(S, X, t, r1, sigma, q):
        # Calculate d1 and d2
        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S / X) + (r1 - q + 0.5 * sigma**2) * t) / sigma_t
        d2 = d1 - sigma_t

        # Calculate Vomma
        vomma_num = S * math.exp(-q * t) * scipy.stats.norm.pdf(d1) * math.sqrt(t) * (d1 * d2)
        vomma_deno = sigma
        vomma = vomma_num / vomma_deno

        return vomma

    @staticmethod
    def calculate_charm(S, X, T, r, sigma, q, opt_type):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Calculate the PDF and CDF values
        pdf_d1 = scipy.stats.norm.pdf(d1)
        cdf_d1 = scipy.stats.norm.cdf(d1)
        cdf_minus_d1 = scipy.stats.norm.cdf(-d1)
        e_qt = math.exp(-q * T)

        # Calculate the charm based on option type
        if opt_type.upper() == "CALL":

            charm_num = q * e_qt * cdf_d1 - e_qt * pdf_d1 * (2 * (r - q) * T - d2 * sigma * math.sqrt(T))
            charm_deno = 2 * T * sigma * math.sqrt(T)

        elif opt_type.upper() == "PUT":
            charm_num = -q * e_qt * cdf_minus_d1 - e_qt * pdf_d1 * (2 * (r - q) * T - d2 * sigma * math.sqrt(T))
            charm_deno = 2 * T * sigma * math.sqrt(T)

        else:
            raise ValueError("opt_type must be 'CALL' or 'PUT'")
        charm = charm_num / charm_deno
        return charm

    @staticmethod
    def calculate_speed(S, X, T, r, sigma, q):
        # Calculate d1
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))

        # Calculate the PDF of d1
        pdf_d1 = scipy.stats.norm.pdf(d1)
        last_term = (d1 / (sigma * math.sqrt(T))) + 1

        # Calculate Speed
        speed_num = -math.exp(-q * T) * pdf_d1 * last_term
        speed_deno = S**2 * sigma * math.sqrt(T)
        speed = speed_num / speed_deno

        return speed

    @staticmethod
    def calculate_veta(S, X, T, r, sigma, q):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Calculate the PDF of d1
        pdf_d1 = scipy.stats.norm.pdf(d1)

        # Calculate Veta
        last_term = q + (((r - q) * d1) / (sigma * math.sqrt(T))) - ((1 + d1 * d2) / (2 * T))
        veta = -S * math.exp(-q * T) * pdf_d1 * math.sqrt(T) * last_term

        return veta

    @staticmethod
    def calculate_ultima(S, X, T, r, sigma, q):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Calculate Vega for the formula
        V = S * math.exp(-q * T) * scipy.stats.norm.pdf(d1) * math.sqrt(T)

        # Calculate Ultima
        ultima = (-V / sigma**2) * (d1 * d2 * (1 - d1 * d2) + d1**2 + d2**2)

        return ultima

    @staticmethod
    def calculate_color(S, X, T, r, sigma, q):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Calculate the PDF of d1
        pdf_d1 = scipy.stats.norm.pdf(d1)

        last_term_last_num = (2 * (r - q) * T - d2 * sigma * math.sqrt(T)) * d1
        last_term_last_deno = sigma * math.sqrt(T)
        last_term = (2 * q * T) + 1 + (last_term_last_num / last_term_last_deno)

        # Calculate Color
        color_num = -math.exp(-q * T) * pdf_d1 * last_term

        color_deno = 2 * S * T * sigma * math.sqrt(T)
        color = color_num / color_deno

        return color
