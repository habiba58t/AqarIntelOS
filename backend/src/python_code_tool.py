# import pandas as pd
# from typing import Dict, Union, Any, Annotated
# from langchain_core.tools import tool, InjectedToolCallId
# from langgraph.types import Command
# import io
# import sys
# import uuid
# from langchain_core.messages import  ToolMessage
# import plotly.express as px
# import plotly.graph_objects as go
# import io
# import contextlib
# from langgraph.prebuilt import InjectedState




# projects_df = pd.read_csv("data/projects_cleaned.csv")
# units_df = pd.read_csv("data/units_cleaned.csv")

# @tool
# def execute_python_query(
#     code: str,
#     tool_call_id: Annotated[str, InjectedToolCallId]
# ) -> Union[str, Command]:
#     """
#     Execute Python code with access to smart analysis functions.
    
#     Available datasets:
#     - units_df: Individual real estate units
#     - projects_df: Real estate projects
    
#     Available smart functions (call these for instant insights):
#     - analyze_prices_by_location(location=None)
#     - compare_unit_types()
#     - find_affordable_options(budget)
#     - analyze_price_trends()
#     - compare_developers(top_n=5)
#     - get_market_summary()
#     - filter_units(location, unit_type, min_price, max_price, bedrooms)
    
#     Examples of code to write:
#         # Get price analysis for all locations
#         result = analyze_prices_by_location()
#         print(result)
        
#         # Compare unit types
#         result = compare_unit_types()
#         print(result)
        
#         # Find affordable options
#         result = find_affordable_options(5000000)
#         print(result)
        
#         # Filter and analyze
#         result = filter_units(location="New Cairo", unit_type="Apartment", bedrooms=3)
#         print(result)
    
#     For custom analysis, use regular pandas:
#         result = units_df.groupby('location')['price'].mean()
#         print(result)
#     """
    
    
#     command_to_return = None


#     def save_plot_to_state(
#       plot_json: dict,
#        ) -> str:
#       """
#         Function exposed to LLM's Python environment.
#         Saves plot to state and returns confirmation message.
#         """
#       nonlocal command_to_return
#       plot_id = str(uuid.uuid4())
#       print(f"💾 Saving plot with ID: {plot_id}")
#       command_to_return= Command(update={
#         "saved_plots": [{"id": plot_id, "data": plot_json}],
#         "messages": [
#             ToolMessage(f"✅ Plot saved with ID {plot_id}", tool_call_id=tool_call_id)
#         ]
#        })
#       return f"Plot saved with ID {plot_id}"
    


#     def analyze_prices_by_location(location=None):
#         """
#         Smart price analysis by location with automatic insights.
        
#         Usage in LLM code:
#             result = analyze_prices_by_location()
#             result = analyze_prices_by_location("New Cairo")
#         """
#         if location:
#             data = units_df[units_df['location'].str.contains(location, case=False, na=False)]
#             title = f"Price Analysis: {location}"
#         else:
#             data = units_df.copy()
#             title = "Price Analysis: All Locations"
        
#         # Calculate statistics
#         stats = data.groupby('location')['price'].agg(['mean', 'median', 'count', 'min', 'max'])
#         stats = stats.sort_values('mean', ascending=False)
        
#         # Create visualization
#         fig = px.box(
#             data,
#             x='location',
#             y='price',
#             title=title,
#             labels={'price': 'Price (EGP)', 'location': 'Location'},
#             color='location',
#             points=False
#         )
        
#         # Save plot
#         save_plot_to_state(fig.to_dict())
        
#         # Generate insights
#         insights = f"""
# 📊 PRICE ANALYSIS BY LOCATION

# 📈 Statistics:
# • Most Expensive: {stats.index[0]} ({stats.iloc[0]['mean']/1_000_000:.2f}M avg)
# • Most Affordable: {stats.index[-1]} ({stats.iloc[-1]['mean']/1_000_000:.2f}M avg)
# • Overall Average: {data['price'].mean()/1_000_000:.2f}M EGP
# • Total Units Analyzed: {len(data)}

# 💡 Key Insights:
# • Price difference: {((stats.iloc[0]['mean'] - stats.iloc[-1]['mean'])/stats.iloc[-1]['mean']*100):.0f}% between highest and lowest
# • Median vs Mean gap: {abs((data['price'].median() - data['price'].mean())/data['price'].mean()*100):.1f}% (indicates price distribution)
# """
        
#         return insights
    
#     def compare_unit_types():
#         """
#         Compare different unit types (Apartment, Villa, Studio, etc.)
        
#         Usage: result = compare_unit_types()
#         """
#         stats = units_df.groupby('unit_type').agg({
#             'price': ['mean', 'median', 'count'],
#             'area_sqm': 'mean'
#         }).round(0)
        
#         stats.columns = ['avg_price', 'median_price', 'count', 'avg_area']
#         stats = stats.sort_values('avg_price', ascending=False)
#         stats['price_per_sqm'] = (stats['avg_price'] / stats['avg_area']).round(0)
        
#         # # Create chart
#         # fig = px.bar(
#         #     stats.reset_index(),
#         #     x='unit_type',
#         #     y='avg_price',
#         #     title='Unit Types: Average Prices',
#         #     labels={'avg_price': 'Average Price (EGP)', 'unit_type': 'Unit Type'},
#         #     color='avg_price',
#         #     text='avg_price'
#         # )
        
#         # fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
#         # save_plot_to_state(fig.to_dict())
        
#         insights = f"""
# 🏠 UNIT TYPE COMPARISON

# 💰 Pricing Analysis:
# """
#         for unit_type, row in stats.iterrows():
#             insights += f"• {unit_type}: {row['avg_price']/1_000_000:.2f}M avg | {int(row['count'])} units | {row['price_per_sqm']:.0f} EGP/sqm\n"
        
#         best_value = stats['price_per_sqm'].idxmin()
#         most_popular = stats['count'].idxmax()
        
#         insights += f"""
# ✨ Smart Recommendations:
# • Best Value: {best_value} ({stats.loc[best_value, 'price_per_sqm']:.0f} EGP/sqm)
# • Most Available: {most_popular} ({int(stats.loc[most_popular, 'count'])} units)
# • Premium Segment: {', '.join(stats[stats['avg_price'] > stats['avg_price'].mean()].index)}
# """
        
#         return insights
    
#     def find_affordable_options(budget):
#         """
#         Find what's available within a budget with smart recommendations.
        
#         Usage: result = find_affordable_options(5000000)  # 5M EGP
#         """
#         affordable = units_df[units_df['price'] <= budget].copy()
        
#         if len(affordable) == 0:
#             return f"❌ No units found within {budget/1_000_000:.1f}M EGP. Minimum available: {units_df['price'].min()/1_000_000:.1f}M"
        
#         # Breakdown
#         by_type = affordable.groupby('unit_type').agg({
#             'unit_code': 'count',
#             'price': 'mean'
#         }).sort_values('unit_code', ascending=False)
        
#         by_location = affordable.groupby('location').agg({
#             'unit_code': 'count',
#             'price': 'mean'
#         }).sort_values('unit_code', ascending=False)
        
#         # Create chart
#         fig = px.pie(
#             by_type.reset_index(),
#             values='unit_code',
#             names='unit_type',
#             title=f'Available Units Within {budget/1_000_000:.1f}M Budget'
#         )
#         save_plot_to_state(fig.to_dict())
        
#         insights = f"""
# 💰 AFFORDABILITY ANALYSIS ({budget/1_000_000:.1f}M EGP)

# 📊 Overview:
# • Total Options: {len(affordable)} units
# • Average Price: {affordable['price'].mean()/1_000_000:.2f}M
# • Your Savings: {(budget - affordable['price'].mean())/1_000_000:.2f}M on average

# 🏠 Best Unit Types:
# """
#         for i, (unit_type, row) in enumerate(by_type.head(3).iterrows(), 1):
#             insights += f"{i}. {unit_type}: {int(row['unit_code'])} units @ {row['price']/1_000_000:.2f}M avg\n"
        
#         insights += f"\n📍 Best Locations:\n"
#         for i, (loc, row) in enumerate(by_location.head(3).iterrows(), 1):
#             insights += f"{i}. {loc}: {int(row['unit_code'])} units @ {row['price']/1_000_000:.2f}M avg\n"
        
#         insights += f"\n💡 Recommendation: Focus on {by_type.index[0]} in {by_location.index[0]} for maximum choice"
        
#         return insights
    
#     def analyze_price_trends():
#         """
#         Analyze price trends by delivery year.
        
#         Usage: result = analyze_price_trends()
#         """
#         data = units_df[units_df['delivery_year'].notna()].copy()
#         data = data[data['delivery_year'] >= 2023]
        
#         trends = data.groupby('delivery_year').agg({
#             'price': ['mean', 'count']
#         }).round(0)
        
#         trends.columns = ['avg_price', 'count']
        
#         # # Create chart
#         # fig = go.Figure()
#         # fig.add_trace(go.Scatter(
#         #     x=trends.index,
#         #     y=trends['avg_price']/1_000_000,
#         #     mode='lines+markers',
#         #     name='Average Price',
#         #     line=dict(width=3),
#         #     marker=dict(size=10)
#         # ))
        
#         # fig.update_layout(
#         #     title='Price Trends by Delivery Year',
#         #     xaxis_title='Delivery Year',
#         #     yaxis_title='Average Price (Million EGP)'
#         # )
        
#         # save_plot_to_state(fig.to_dict())
        
#         insights = f"""
# 📈 PRICE TRENDS BY DELIVERY YEAR

# 📊 Year-by-Year:
# """
#         for year, row in trends.iterrows():
#             insights += f"• {int(year)}: {row['avg_price']/1_000_000:.2f}M avg ({int(row['count'])} units)\n"
        
#         if len(trends) > 1:
#             change = ((trends.iloc[-1]['avg_price'] - trends.iloc[0]['avg_price']) / trends.iloc[0]['avg_price'] * 100)
#             insights += f"\n💡 Trend: {'📈 Growing' if change > 0 else '📉 Declining'} market ({abs(change):.1f}% change)"
        
#         return insights
    
#     def compare_developers(top_n=5):
#         """
#         Compare top developers in the market.
        
#         Usage: result = compare_developers(5)
#         """
#         dev_stats = projects_df.groupby('developer').agg({
#             'name': 'count',
#             'avg_price': 'mean',
#             'unit_count': 'sum'
#         }).sort_values('name', ascending=False).head(top_n)
        
#         dev_stats.columns = ['projects', 'avg_price', 'total_units']
        
#         # # Create chart
#         # fig = px.bar(
#         #     dev_stats.reset_index(),
#         #     x='developer',
#         #     y='projects',
#         #     title=f'Top {top_n} Developers',
#         #     color='avg_price',
#         #     text='projects'
#         # )
        
#         # save_plot_to_state(fig.to_dict())
        
#         insights = f"""
# 🏢 TOP {top_n} DEVELOPERS

# 📊 Rankings:
# """
#         for i, (dev, row) in enumerate(dev_stats.iterrows(), 1):
#             insights += f"{i}. {dev}\n"
#             insights += f"   • Projects: {int(row['projects'])} | Units: {int(row['total_units'])} | Avg: {row['avg_price']/1_000_000:.2f}M\n"
        
#         premium = dev_stats[dev_stats['avg_price'] > dev_stats['avg_price'].mean()]
#         insights += f"\n💎 Premium Developers: {', '.join(premium.index)}"
        
#         return insights
    
#     def get_market_summary():
#         """
#         Get comprehensive market overview.
        
#         Usage: result = get_market_summary()
#         """
#         insights = f"""
# 🏘️ REAL ESTATE MARKET SUMMARY

# 📊 Market Size:
# • Total Units: {len(units_df):,}
# • Total Projects: {len(projects_df)}
# • Active Developers: {projects_df['developer'].nunique()}

# 💰 Pricing:
# • Average Unit Price: {units_df['price'].mean()/1_000_000:.2f}M EGP
# • Median Price: {units_df['price'].median()/1_000_000:.2f}M EGP
# • Price Range: {units_df['price'].min()/1_000_000:.1f}M - {units_df['price'].max()/1_000_000:.1f}M

# 🏠 Unit Types:
# """
#         type_dist = units_df['unit_type'].value_counts()
#         for unit_type, count in type_dist.head(5).items():
#             insights += f"• {unit_type}: {count:,} units ({count/len(units_df)*100:.1f}%)\n"
        
#         insights += f"""
# 📍 Top Locations:
# """
#         loc_dist = units_df['location'].value_counts()
#         for location, count in loc_dist.head(5).items():
#             insights += f"• {location}: {count:,} units\n"
        
#         # # Create overview chart
#         # fig = px.histogram(
#         #     units_df,
#         #     x='price',
#         #     nbins=50,
#         #     title='Market Price Distribution'
#         # )
#         # save_plot_to_state(fig.to_dict())
        
#         return insights
    
#     def filter_units(location=None, unit_type=None, min_price=None, max_price=None, bedrooms=None):
#         """
#         Smart filtering with automatic insights.
        
#         Usage:
#             result = filter_units(location="New Cairo", unit_type="Apartment", bedrooms=3)
#             result = filter_units(min_price=3000000, max_price=5000000)
#         """
#         filtered = units_df.copy()
        
#         filters_applied = []
        
#         if location:
#             filtered = filtered[filtered['location'].str.contains(location, case=False, na=False)]
#             filters_applied.append(f"Location: {location}")
        
#         if unit_type:
#             filtered = filtered[filtered['unit_type'].str.contains(unit_type, case=False, na=False)]
#             filters_applied.append(f"Type: {unit_type}")
        
#         if min_price:
#             filtered = filtered[filtered['price'] >= min_price]
#             filters_applied.append(f"Min Price: {min_price/1_000_000:.1f}M")
        
#         if max_price:
#             filtered = filtered[filtered['price'] <= max_price]
#             filters_applied.append(f"Max Price: {max_price/1_000_000:.1f}M")
        
#         if bedrooms:
#             filtered = filtered[filtered['bedrooms'] == bedrooms]
#             filters_applied.append(f"Bedrooms: {bedrooms}")
        
#         if len(filtered) == 0:
#             return f"❌ No units found matching: {', '.join(filters_applied)}"
        
#         insights = f"""
# 🔍 FILTERED RESULTS

# 📋 Filters Applied: {', '.join(filters_applied)}

# 📊 Results:
# • Found: {len(filtered)} units
# • Price Range: {filtered['price'].min()/1_000_000:.1f}M - {filtered['price'].max()/1_000_000:.1f}M
# • Average: {filtered['price'].mean()/1_000_000:.2f}M
# • Median: {filtered['price'].median()/1_000_000:.2f}M

# 🏠 Top Options:
# """
        
#         # Show top 5 cheapest
#         top_options = filtered.nsmallest(5, 'price')[['project_name', 'location', 'price', 'area_sqm', 'bedrooms']]
#         for idx, row in top_options.iterrows():
#             insights += f"• {row['project_name']}: {row['price']/1_000_000:.2f}M | {row['area_sqm']:.0f} sqm | {row['bedrooms']} BR\n"
        
#         return insights











#     # Capture stdout
#     old_stdout = sys.stdout
#     captured_output = io.StringIO()
#     sys.stdout = captured_output

#     try:
        
#         namespace = {
#             "pd": pd,
#             "units_df": units_df,
#             "projects_df": projects_df,
#             "__builtins__": __builtins__,
#             "save_plot_in_state": save_plot_to_state,
#             "analyze_prices_by_location": analyze_prices_by_location,
#             "compare_unit_types": compare_unit_types,  
#             "find_affordable_options": find_affordable_options,
#             "analyze_price_trends":analyze_price_trends,
#             "compare_developers": compare_developers,
#             "get_market_summary":get_market_summary,
#             "filter_units":filter_units
#         }

#         code_cleaned = code.replace('.show()', '')
#         code_cleaned = code_cleaned.replace('.write_image(', '# .write_image(')
#         code_cleaned = code_cleaned.replace('.write_html(', '# .write_html(')
                

        

#         exec(code_cleaned , namespace)

#         # Restore stdout
#         sys.stdout = old_stdout
#         output = captured_output.getvalue()

#         # ✅ CRITICAL: Check if Command was created
#         if command_to_return is not None:
#             print("✅ Returning Command to update state")
#             return command_to_return

#         # If no print output, try to get a 'result' variable or provide confirmation
#         if not output.strip():
#             if "result" in namespace:
#                 output = str(namespace["result"])
#             else:
#                 output = "Code executed successfully but produced no output. Use print() to display results."

#         return output

#     except Exception as e:
#         # Ensure stdout is restored on exceptions
#         sys.stdout = old_stdout
#         return f"Error executing code: {str(e)}"



import pandas as pd
from typing import Dict, Union, Any, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
import io
import sys
import uuid
from langchain_core.messages import ToolMessage
import plotly.express as px
import plotly.graph_objects as go
import io
import contextlib
from langgraph.prebuilt import InjectedState

projects_df = pd.read_csv("data/projects_cleaned.csv")
units_df = pd.read_csv("data/units_cleaned.csv")

@tool
def execute_python_query(
    code: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Union[str, Command]:
    """
    Execute Python code with access to smart analysis functions.
    
    Available datasets:
    - units_df: Individual real estate units
    - projects_df: Real estate projects
    
    Available smart functions (call these for instant insights):
    - analyze_prices_by_location(location=None)
    - compare_unit_types()
    - find_affordable_options(budget)
    - analyze_price_trends()
    - compare_developers(top_n=5)
    - get_market_summary()
    - filter_units(location, unit_type, min_price, max_price, bedrooms)
    """
    
    command_to_return = None
    plots_to_save = []

    def save_plot_to_state(plot_json: dict) -> str:
        """
        Function exposed to LLM's Python environment.
        Saves plot to state and returns confirmation message.
        """
        nonlocal plots_to_save
        plot_id = str(uuid.uuid4())
        print(f"💾 Saving plot with ID: {plot_id}")
        plots_to_save.append({"id": plot_id, "data": plot_json})
        return f"Plot saved with ID {plot_id}"

    def analyze_prices_by_location(location=None):
        """Smart price analysis by location with automatic insights."""
        if location:
            data = units_df[units_df['location'].str.contains(location, case=False, na=False)]
            title = f"Price Analysis: {location}"
        else:
            data = units_df.copy()
            title = "Price Analysis: All Locations"
        
        # Calculate statistics
        stats = data.groupby('location')['price'].agg(['mean', 'median', 'count', 'min', 'max'])
        stats = stats.sort_values('mean', ascending=False)
        
        # Create visualization
        fig = px.box(
            data,
            x='location',
            y='price',
            title=title,
            labels={'price': 'Price (EGP)', 'location': 'Location'},
            color='location',
            points=False
        )
        
        # Save plot
        save_plot_to_state(fig.to_dict())
        
        # Generate insights
        insights = f"""
📊 PRICE ANALYSIS BY LOCATION

📈 Statistics:
• Most Expensive: {stats.index[0]} ({stats.iloc[0]['mean']/1_000_000:.2f}M avg)
• Most Affordable: {stats.index[-1]} ({stats.iloc[-1]['mean']/1_000_000:.2f}M avg)
• Overall Average: {data['price'].mean()/1_000_000:.2f}M EGP
• Total Units Analyzed: {len(data)}

💡 Key Insights:
• Price difference: {((stats.iloc[0]['mean'] - stats.iloc[-1]['mean'])/stats.iloc[-1]['mean']*100):.0f}% between highest and lowest
• Median vs Mean gap: {abs((data['price'].median() - data['price'].mean())/data['price'].mean()*100):.1f}% (indicates price distribution)
"""
        return insights
    
    def compare_unit_types():
        """Compare different unit types (Apartment, Villa, Studio, etc.)"""
        stats = units_df.groupby('unit_type').agg({
            'price': ['mean', 'median', 'count'],
            'area_sqm': 'mean'
        }).round(0)
        
        stats.columns = ['avg_price', 'median_price', 'count', 'avg_area']
        stats = stats.sort_values('avg_price', ascending=False)
        stats['price_per_sqm'] = (stats['avg_price'] / stats['avg_area']).round(0)
        
        insights = f"""
🏠 UNIT TYPE COMPARISON

💰 Pricing Analysis:
"""
        for unit_type, row in stats.iterrows():
            insights += f"• {unit_type}: {row['avg_price']/1_000_000:.2f}M avg | {int(row['count'])} units | {row['price_per_sqm']:.0f} EGP/sqm\n"
        
        best_value = stats['price_per_sqm'].idxmin()
        most_popular = stats['count'].idxmax()
        
        insights += f"""
✨ Smart Recommendations:
• Best Value: {best_value} ({stats.loc[best_value, 'price_per_sqm']:.0f} EGP/sqm)
• Most Available: {most_popular} ({int(stats.loc[most_popular, 'count'])} units)
• Premium Segment: {', '.join(stats[stats['avg_price'] > stats['avg_price'].mean()].index)}
"""
        return insights
    
    def find_affordable_options(budget):
        """Find what's available within a budget with smart recommendations."""
        affordable = units_df[units_df['price'] <= budget].copy()
        
        if len(affordable) == 0:
            return f"❌ No units found within {budget/1_000_000:.1f}M EGP. Minimum available: {units_df['price'].min()/1_000_000:.1f}M"
        
        # Breakdown
        by_type = affordable.groupby('unit_type').agg({
            'unit_code': 'count',
            'price': 'mean'
        }).sort_values('unit_code', ascending=False)
        
        by_location = affordable.groupby('location').agg({
            'unit_code': 'count',
            'price': 'mean'
        }).sort_values('unit_code', ascending=False)
        
        # Create chart
        fig = px.pie(
            by_type.reset_index(),
            values='unit_code',
            names='unit_type',
            title=f'Available Units Within {budget/1_000_000:.1f}M Budget'
        )
        save_plot_to_state(fig.to_dict())
        
        insights = f"""
💰 AFFORDABILITY ANALYSIS ({budget/1_000_000:.1f}M EGP)

📊 Overview:
• Total Options: {len(affordable)} units
• Average Price: {affordable['price'].mean()/1_000_000:.2f}M
• Your Savings: {(budget - affordable['price'].mean())/1_000_000:.2f}M on average

🏠 Best Unit Types:
"""
        for i, (unit_type, row) in enumerate(by_type.head(3).iterrows(), 1):
            insights += f"{i}. {unit_type}: {int(row['unit_code'])} units @ {row['price']/1_000_000:.2f}M avg\n"
        
        insights += f"\n📍 Best Locations:\n"
        for i, (loc, row) in enumerate(by_location.head(3).iterrows(), 1):
            insights += f"{i}. {loc}: {int(row['unit_code'])} units @ {row['price']/1_000_000:.2f}M avg\n"
        
        insights += f"\n💡 Recommendation: Focus on {by_type.index[0]} in {by_location.index[0]} for maximum choice"
        
        return insights
    
    def analyze_price_trends():
        """Analyze price trends by delivery year."""
        data = units_df[units_df['delivery_year'].notna()].copy()
        data = data[data['delivery_year'] >= 2023]
        
        trends = data.groupby('delivery_year').agg({
            'price': ['mean', 'count']
        }).round(0)
        
        trends.columns = ['avg_price', 'count']
        
        insights = f"""
📈 PRICE TRENDS BY DELIVERY YEAR

📊 Year-by-Year:
"""
        for year, row in trends.iterrows():
            insights += f"• {int(year)}: {row['avg_price']/1_000_000:.2f}M avg ({int(row['count'])} units)\n"
        
        if len(trends) > 1:
            change = ((trends.iloc[-1]['avg_price'] - trends.iloc[0]['avg_price']) / trends.iloc[0]['avg_price'] * 100)
            insights += f"\n💡 Trend: {'📈 Growing' if change > 0 else '📉 Declining'} market ({abs(change):.1f}% change)"
        
        return insights
    
    def compare_developers(top_n=5):
        """Compare top developers in the market."""
        dev_stats = projects_df.groupby('developer').agg({
            'name': 'count',
            'avg_price': 'mean',
            'unit_count': 'sum'
        }).sort_values('name', ascending=False).head(top_n)
        
        dev_stats.columns = ['projects', 'avg_price', 'total_units']
        
        insights = f"""
🏢 TOP {top_n} DEVELOPERS

📊 Rankings:
"""
        for i, (dev, row) in enumerate(dev_stats.iterrows(), 1):
            insights += f"{i}. {dev}\n"
            insights += f"   • Projects: {int(row['projects'])} | Units: {int(row['total_units'])} | Avg: {row['avg_price']/1_000_000:.2f}M\n"
        
        premium = dev_stats[dev_stats['avg_price'] > dev_stats['avg_price'].mean()]
        insights += f"\n💎 Premium Developers: {', '.join(premium.index)}"
        
        return insights
    
    def get_market_summary():
        """Get comprehensive market overview."""
        insights = f"""
🏘️ REAL ESTATE MARKET SUMMARY

📊 Market Size:
• Total Units: {len(units_df):,}
• Total Projects: {len(projects_df)}
• Active Developers: {projects_df['developer'].nunique()}

💰 Pricing:
• Average Unit Price: {units_df['price'].mean()/1_000_000:.2f}M EGP
• Median Price: {units_df['price'].median()/1_000_000:.2f}M EGP
• Price Range: {units_df['price'].min()/1_000_000:.1f}M - {units_df['price'].max()/1_000_000:.1f}M

🏠 Unit Types:
"""
        type_dist = units_df['unit_type'].value_counts()
        for unit_type, count in type_dist.head(5).items():
            insights += f"• {unit_type}: {count:,} units ({count/len(units_df)*100:.1f}%)\n"
        
        insights += f"""
📍 Top Locations:
"""
        loc_dist = units_df['location'].value_counts()
        for location, count in loc_dist.head(5).items():
            insights += f"• {location}: {count:,} units\n"
        
        return insights
    
    def filter_units(location=None, unit_type=None, min_price=None, max_price=None, bedrooms=None):
        """Smart filtering with automatic insights."""
        filtered = units_df.copy()
        filters_applied = []
        
        if location:
            filtered = filtered[filtered['location'].str.contains(location, case=False, na=False)]
            filters_applied.append(f"Location: {location}")
        
        if unit_type:
            filtered = filtered[filtered['unit_type'].str.contains(unit_type, case=False, na=False)]
            filters_applied.append(f"Type: {unit_type}")
        
        if min_price:
            filtered = filtered[filtered['price'] >= min_price]
            filters_applied.append(f"Min Price: {min_price/1_000_000:.1f}M")
        
        if max_price:
            filtered = filtered[filtered['price'] <= max_price]
            filters_applied.append(f"Max Price: {max_price/1_000_000:.1f}M")
        
        if bedrooms:
            filtered = filtered[filtered['bedrooms'] == bedrooms]
            filters_applied.append(f"Bedrooms: {bedrooms}")
        
        if len(filtered) == 0:
            return f"❌ No units found matching: {', '.join(filters_applied)}"
        
        insights = f"""
🔍 FILTERED RESULTS

📋 Filters Applied: {', '.join(filters_applied)}

📊 Results:
• Found: {len(filtered)} units
• Price Range: {filtered['price'].min()/1_000_000:.1f}M - {filtered['price'].max()/1_000_000:.1f}M
• Average: {filtered['price'].mean()/1_000_000:.2f}M
• Median: {filtered['price'].median()/1_000_000:.2f}M

🏠 Top Options:
"""
        top_options = filtered.nsmallest(5, 'price')[['project_name', 'location', 'price', 'area_sqm', 'bedrooms']]
        for idx, row in top_options.iterrows():
            insights += f"• {row['project_name']}: {row['price']/1_000_000:.2f}M | {row['area_sqm']:.0f} sqm | {row['bedrooms']} BR\n"
        
        return insights

    # Capture stdout
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        namespace = {
            "pd": pd,
            "units_df": units_df,
            "projects_df": projects_df,
            "__builtins__": __builtins__,
            "save_plot_in_state": save_plot_to_state,
            "analyze_prices_by_location": analyze_prices_by_location,
            "compare_unit_types": compare_unit_types,  
            "find_affordable_options": find_affordable_options,
            "analyze_price_trends": analyze_price_trends,
            "compare_developers": compare_developers,
            "get_market_summary": get_market_summary,
            "filter_units": filter_units
        }

        smart_functions = [
            'analyze_prices_by_location', 'compare_unit_types', 
            'find_affordable_options', 'analyze_price_trends',
            'compare_developers', 'get_market_summary', 'filter_units'
        ]
        
        

        code_cleaned = code.replace('.show()', '')
        code_cleaned = code_cleaned.replace('.write_image(', '# .write_image(')
        code_cleaned = code_cleaned.replace('.write_html(', '# .write_html(')
        
        for func in smart_functions:
            if f"{func}(" in code_cleaned and f"print({func}" not in code_cleaned:
                # Wrap the function call with print
                code_cleaned = f"result = {code_cleaned}\nprint(result)"
                break

        exec(code_cleaned, namespace)

        # Restore stdout
        sys.stdout = old_stdout
        output = captured_output.getvalue()

        # If no print output, try to get a 'result' variable
        if not output.strip():
            if "result" in namespace:
                output = str(namespace["result"])
            else:
                output = "Code executed successfully but produced no output. Use print() to display results."

        # ✅ KEY FIX: Return Command with BOTH plots AND text output
        if plots_to_save:
            print(f"✅ Returning Command with {len(plots_to_save)} plots and text output")
            return Command(
                update={
                    "saved_plots": plots_to_save,
                    "messages": [
                        ToolMessage(content=output, tool_call_id=tool_call_id)
                    ]
                }
            )
        
        # If no plots, just return the text output
        return output

    except Exception as e:
        sys.stdout = old_stdout
        return f"Error executing code: {str(e)}"