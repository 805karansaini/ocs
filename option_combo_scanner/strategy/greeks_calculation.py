from collections import defaultdict
import datetime
import math
import scipy.stats

from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
class CalcluateGreeks:
    def compute_all_greeks(combination, list_of_config_leg_object):

        list_of_greeks_dicts_for_leg_tuple = [] # List to store dictionaries of Greeks for each leg
        net_greeks = defaultdict(float)
        # Loop over the leg tuple of each combination
        for leg_tuple, config_leg_object in zip(combination, list_of_config_leg_object):
            # Unpack the values stored in tuple
            _,strike,_,_,expiry,_,_,_,_,vega,theta,gamma,underlying_price = leg_tuple

            # Calcluate the time to expiration for the greeks
            current_date = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj = datetime.datetime.strptime(current_date, "%Y%m%d")

            expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
            time_to_expiration = (abs(current_date_obj - expiry_date_obj).days)/365

            # Get the IV for the greeks calcluation
            sigma = Utils.get_implied_volatility(underlying_price, StrategyVariables.riskfree_rate1, 0, time_to_expiration, strike, underlying_price, config_leg_object.right)
            # Calcluate Vanna greeks for each leg_tuple
            vanna = CalcluateGreeks.calculate_vanna(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0)
            # Calcluate Zomma greeks for each leg_tuple
            zomma = CalcluateGreeks.calculate_zomma(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0)
            # Calcluate Vomma greeks for each leg_tuple
            vomma = CalcluateGreeks.calculate_vomma(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0)
            # Calcluate Charm greeks for each leg_tuple
            charm = CalcluateGreeks.calculate_charm(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0, config_leg_object.right)
            # Calcluate speed greeks for each leg_tuple
            speed = CalcluateGreeks.calculate_speed(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0)
            # Calcluate color greeks for each leg_tuple
            color = CalcluateGreeks.calculate_color(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0)
            # Calcluate veta greeks for each leg_tuple
            veta = CalcluateGreeks.calculate_veta(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0)
            # Calcluate ultima greeks for each leg_tuple
            ultima = CalcluateGreeks.calculate_ultima(underlying_price, strike, time_to_expiration, StrategyVariables.riskfree_rate1, sigma, 0)
            
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
                    net_greeks[greek] += float(value)
                elif config_leg_object.action.upper() == "SELL":
                    net_greeks[greek] -= float(value)

            # Append the dictionary of Greeks for the current leg to the list
            list_of_greeks_dicts_for_leg_tuple.append(greeks_dict)
        return net_greeks

            




    


    @staticmethod
    def calculate_vanna(S, X, t, r1, sigma, q):
        # Calculate d1 and d2
        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S / X) + (r1 - q + 0.5 * sigma ** 2) * t) / sigma_t
        d2 = d1 - sigma_t
        
        # Calculate Vanna
        vanna = -math.exp(-q * t) * scipy.stats.norm.pdf(d1) * d2 / sigma
        
        return vanna
    
    
    @staticmethod
    def calculate_zomma(S, X, t, r1, sigma, q):
        # Calculate d1 and d2
        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S / X) + (r1 - q + 0.5 * sigma ** 2) * t) / sigma_t
        d2 = d1 - sigma_t
        
        # Calculate Zomma
        zomma = (math.exp(-q * t) * scipy.stats.norm.pdf(d1)) / (S * sigma**2 * math.sqrt(t)) * (d1 * d2 - 1)
        
        return zomma
    
    @staticmethod
    def calculate_vomma(S, X, t, r1, sigma, q):
        # Calculate d1 and d2
        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S / X) + (r1 - q + 0.5 * sigma ** 2) * t) / sigma_t
        d2 = d1 - sigma_t
        
        # Calculate Vomma
        vomma = S * math.exp(-q * t) * scipy.stats.norm.pdf(d1) * math.sqrt(t) * (d1 * d2 / sigma)
        
        return vomma
    
    @staticmethod
    def calculate_charm(S, X, T, r, sigma, q, opt_type):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Calculate the PDF and CDF values
        pdf_d1 = scipy.stats.norm.pdf(d1)
        cdf_d1 = scipy.stats.norm.cdf(d1)
        cdf_minus_d1 = scipy.stats.norm.cdf(-d1)
        
        # Calculate the charm based on option type
        if opt_type.upper() == "CALL":
            charm = q * math.exp(-q * T) * cdf_d1 - math.exp(-q * T) * pdf_d1 * \
                    (2 * (r - q) * T - d2 * sigma * math.sqrt(T)) / (2 * T * sigma * math.sqrt(T))
        elif opt_type.upper() == "PUT":
            charm = -q * math.exp(-q * T) * cdf_minus_d1 - math.exp(-q * T) * pdf_d1 * \
                    (2 * (r - q) * T - d2 * sigma * math.sqrt(T)) / (2 * T * sigma * math.sqrt(T))
        else:
            raise ValueError("opt_type must be 'CALL' or 'PUT'")
        
        return charm
    
    @staticmethod
    def calculate_speed(S, X, T, r, sigma, q):
        # Calculate d1
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        
        # Calculate the PDF of d1
        pdf_d1 = scipy.stats.norm.pdf(d1)
        
        # Calculate Speed
        speed = -math.exp(-q * T) * pdf_d1 / (S**2 * sigma * math.sqrt(T)) * (d1 / (sigma * math.sqrt(T)) + 1)
        
        return speed
    
    @staticmethod
    def calculate_veta(S, X, T, r, sigma, q):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Calculate the PDF of d1
        pdf_d1 = scipy.stats.norm.pdf(d1)
        
        # Calculate Veta
        veta = -S * math.exp(-q * T) * pdf_d1 * math.sqrt(T) * \
            (q + ((r - q) * d1) / (sigma * math.sqrt(T)) - (1 + d1 * d2) / (2 * T))
        
        return veta
    
    @staticmethod
    def calculate_ultima(S, X, T, r, sigma, q):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Calculate Vega for the formula
        V = S * math.exp(-q * T) * scipy.stats.norm.pdf(d1) * math.sqrt(T)
        
        # Calculate Ultima
        ultima = -(V / sigma**2) * (d1 * d2 * (1 - d1 * d2) + d1**2 + d2**2)
        
        return ultima
    
    @staticmethod
    def calculate_color(S, X, T, r, sigma, q):
        # Calculate d1 and d2
        d1 = (math.log(S / X) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Calculate the PDF of d1
        pdf_d1 = scipy.stats.norm.pdf(d1)
        
        # Calculate Color
        color = -math.exp(-q * T) * pdf_d1 / (2 * S * sigma * math.sqrt(T)) * \
                (2 * q * T + 1 + ((2 * (r - q) * T - d2 * sigma * math.sqrt(T)) / (sigma * math.sqrt(T)) * d1))
        
        return color
    