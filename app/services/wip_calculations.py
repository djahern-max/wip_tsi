# app/services/wip_calculations.py
from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel


class WIPCalculator:
    """
    Handles all WIP calculations and field dependencies
    """

    @staticmethod
    def calculate_contract_fields(
        original_contract_amount: Optional[Decimal],
        change_order_amount: Optional[Decimal],
        prior_month_total_contract: Optional[Decimal],
    ) -> Dict[str, Optional[Decimal]]:
        """Calculate contract-related fields"""

        # Total contract = original + change orders
        total_contract = None
        if original_contract_amount is not None and change_order_amount is not None:
            total_contract = original_contract_amount + change_order_amount
        elif original_contract_amount is not None and change_order_amount is None:
            total_contract = original_contract_amount

        # Contract variance = current - prior month
        contract_variance = None
        if total_contract is not None and prior_month_total_contract is not None:
            contract_variance = total_contract - prior_month_total_contract

        return {
            "current_month_total_contract_amount": total_contract,
            "current_vs_prior_contract_variance": contract_variance,
        }

    @staticmethod
    def calculate_cost_fields(
        cost_to_date: Optional[Decimal],
        estimated_cost_to_complete: Optional[Decimal],
        prior_month_estimated_final_cost: Optional[Decimal],
    ) -> Dict[str, Optional[Decimal]]:
        """Calculate cost-related fields"""

        # Estimated final cost = cost to date + estimated cost to complete
        estimated_final_cost = None
        if cost_to_date is not None and estimated_cost_to_complete is not None:
            estimated_final_cost = cost_to_date + estimated_cost_to_complete

        # Final cost variance = current - prior month
        final_cost_variance = None
        if (
            estimated_final_cost is not None
            and prior_month_estimated_final_cost is not None
        ):
            final_cost_variance = (
                estimated_final_cost - prior_month_estimated_final_cost
            )

        return {
            "current_month_estimated_final_cost": estimated_final_cost,
            "current_vs_prior_estimated_final_cost_variance": final_cost_variance,
        }

    @staticmethod
    def calculate_us_gaap_fields(
        total_contract_amount: Optional[Decimal],
        cost_to_date: Optional[Decimal],
        estimated_final_cost: Optional[Decimal],
    ) -> Dict[str, Optional[Decimal]]:
        """Calculate US GAAP revenue recognition fields"""

        # US GAAP % completion = cost to date / estimated final cost
        percent_completion = None
        if (
            cost_to_date is not None
            and estimated_final_cost is not None
            and estimated_final_cost > 0
        ):
            percent_completion = (cost_to_date / estimated_final_cost * 100).quantize(
                Decimal("0.01")
            )

        # Revenue earned = contract amount * % completion
        revenue_earned = None
        if total_contract_amount is not None and percent_completion is not None:
            revenue_earned = (
                total_contract_amount * percent_completion / 100
            ).quantize(Decimal("0.01"))

        # Job margin to date = revenue earned - cost to date
        job_margin_to_date = None
        if revenue_earned is not None and cost_to_date is not None:
            job_margin_to_date = revenue_earned - cost_to_date

        # Job margin as % of sales
        job_margin_percent_sales = None
        if (
            job_margin_to_date is not None
            and revenue_earned is not None
            and revenue_earned > 0
        ):
            job_margin_percent_sales = (
                job_margin_to_date / revenue_earned * 100
            ).quantize(Decimal("0.01"))

        return {
            "us_gaap_percent_completion": percent_completion,
            "revenue_earned_to_date_us_gaap": revenue_earned,
            "estimated_job_margin_to_date_us_gaap": job_margin_to_date,
            "estimated_job_margin_to_date_percent_sales": job_margin_percent_sales,
        }

    @staticmethod
    def calculate_job_margin_fields(
        total_contract_amount: Optional[Decimal],
        estimated_final_cost: Optional[Decimal],
        prior_month_job_margin: Optional[Decimal],
    ) -> Dict[str, Optional[Decimal]]:
        """Calculate job margin at completion fields"""

        # Job margin at completion = contract amount - estimated final cost
        job_margin_at_completion = None
        if total_contract_amount is not None and estimated_final_cost is not None:
            job_margin_at_completion = total_contract_amount - estimated_final_cost

        # Job margin variance = current - prior month
        job_margin_variance = None
        if job_margin_at_completion is not None and prior_month_job_margin is not None:
            job_margin_variance = job_margin_at_completion - prior_month_job_margin

        # Job margin as % of sales
        job_margin_percent_sales = None
        if (
            job_margin_at_completion is not None
            and total_contract_amount is not None
            and total_contract_amount > 0
        ):
            job_margin_percent_sales = (
                job_margin_at_completion / total_contract_amount * 100
            ).quantize(Decimal("0.01"))

        return {
            "current_month_estimated_job_margin_at_completion": job_margin_at_completion,
            "current_vs_prior_estimated_job_margin": job_margin_variance,
            "current_month_estimated_job_margin_percent_sales": job_margin_percent_sales,
        }

    @staticmethod
    def calculate_wip_adjustments(
        revenue_earned: Optional[Decimal],
        cost_to_date: Optional[Decimal],
        billed_to_date: Optional[Decimal],
    ) -> Dict[str, Optional[Decimal]]:
        """Calculate WIP adjustment fields"""

        costs_in_excess = None
        billings_in_excess = None

        if (
            revenue_earned is not None
            and billed_to_date is not None
            and cost_to_date is not None
        ):
            # If costs > revenue earned, we have costs in excess
            if cost_to_date > revenue_earned:
                costs_in_excess = cost_to_date - revenue_earned

            # If billings > revenue earned, we have billings in excess
            if billed_to_date > revenue_earned:
                billings_in_excess = billed_to_date - revenue_earned

        return {
            "current_month_costs_in_excess_billings": costs_in_excess,
            "current_month_billings_excess_revenue": billings_in_excess,
        }

    @classmethod
    def calculate_all_fields(cls, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all dependent fields based on input data
        This is the main method to call when creating/updating WIP records
        """
        result = input_data.copy()

        # 1. Calculate contract fields
        contract_calcs = cls.calculate_contract_fields(
            input_data.get("current_month_original_contract_amount"),
            input_data.get("current_month_change_order_amount"),
            input_data.get("prior_month_total_contract_amount"),
        )
        result.update(contract_calcs)

        # 2. Calculate cost fields
        cost_calcs = cls.calculate_cost_fields(
            input_data.get("current_month_cost_to_date"),
            input_data.get("current_month_estimated_cost_to_complete"),
            input_data.get("prior_month_estimated_final_cost"),
        )
        result.update(cost_calcs)

        # 3. Calculate US GAAP fields
        us_gaap_calcs = cls.calculate_us_gaap_fields(
            result.get("current_month_total_contract_amount"),
            input_data.get("current_month_cost_to_date"),
            result.get("current_month_estimated_final_cost"),
        )
        result.update(us_gaap_calcs)

        # 4. Calculate job margin fields
        job_margin_calcs = cls.calculate_job_margin_fields(
            result.get("current_month_total_contract_amount"),
            result.get("current_month_estimated_final_cost"),
            input_data.get("prior_month_estimated_job_margin_at_completion"),
        )
        result.update(job_margin_calcs)

        # 5. Calculate WIP adjustments
        wip_calcs = cls.calculate_wip_adjustments(
            result.get("revenue_earned_to_date_us_gaap"),
            input_data.get("current_month_cost_to_date"),
            input_data.get("current_month_revenue_billed_to_date"),
        )
        result.update(wip_calcs)

        return result


# Example usage and validation
class WIPInputData(BaseModel):
    """Input data for WIP calculations - only the fields users actually enter"""

    # Required input fields (users must enter these)
    current_month_original_contract_amount: Optional[Decimal] = None
    current_month_change_order_amount: Optional[Decimal] = None
    current_month_cost_to_date: Optional[Decimal] = None
    current_month_estimated_cost_to_complete: Optional[Decimal] = None
    current_month_revenue_billed_to_date: Optional[Decimal] = None

    # Prior month data for comparisons (from previous WIP snapshot)
    prior_month_total_contract_amount: Optional[Decimal] = None
    prior_month_estimated_final_cost: Optional[Decimal] = None
    prior_month_estimated_job_margin_at_completion: Optional[Decimal] = None

    # Optional manual overrides (if user wants to override calculations)
    current_month_addl_entry_required: Optional[Decimal] = None
