from decimal import Decimal, ROUND_HALF_UP

def quantize_2(val) -> Decimal:
    """Округление до 2 знаков (копейки) по банковскому/арифметическому правилу."""
    if val is None:
        return Decimal('0.00')
    d = Decimal(str(val))
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def quantize_3(val) -> Decimal:
    """Округление до 3 знаков (граммы/миллилитры)."""
    if val is None:
        return Decimal('0.000')
    d = Decimal(str(val))
    return d.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


class PackagingCalculationService:
    @staticmethod
    def calculate_item_values(
        raw_amount: float or Decimal,
        raw_price: float or Decimal,
        raw_sum: float or Decimal,
        packaging_coefficient: float or Decimal = 1.0,
        target_iiko_amount: float or Decimal = None,
    ) -> dict:
        """
        Вычисляет складские показатели для iiko на основе сырых данных, коэффициента фасовки
        или прямого целевого количества в iiko (например, 15 кг рыбы -> 6 штук).
        Устраняет погрешности копеек и сохраняет точный баланс строки поставщика.
        """
        raw_amount_dec = quantize_3(raw_amount)
        raw_price_dec = quantize_2(raw_price)
        raw_sum_dec = quantize_2(raw_sum)

        # Если сумма не была указана явно, рассчитываем ее из raw_amount * raw_price
        if raw_sum_dec == Decimal('0.00') and raw_amount_dec > 0 and raw_price_dec > 0:
            raw_sum_dec = quantize_2(raw_amount_dec * raw_price_dec)

        # Двусторонний пересчет:
        # Если передано прямое целевое количество в iiko (target_iiko_amount):
        # вычисляем коэффициент фасовки K = target_iiko_amount / raw_amount
        if target_iiko_amount is not None and Decimal(str(target_iiko_amount)) > Decimal('0.000'):
            iiko_amount = quantize_3(target_iiko_amount)
            if raw_amount_dec > Decimal('0.000'):
                coeff_dec = quantize_3(iiko_amount / raw_amount_dec)
            else:
                coeff_dec = Decimal('1.000')
        else:
            coeff_dec = quantize_3(packaging_coefficient or 1.0)
            if coeff_dec <= Decimal('0.000'):
                coeff_dec = Decimal('1.000')
            iiko_amount = quantize_3(raw_amount_dec * coeff_dec)

        # Расчет цены за 1 базовую единицу iiko
        if iiko_amount > Decimal('0.000'):
            # Цена за базовую единицу = сырая сумма / итоговое количество в базовых единицах
            iiko_price = quantize_2(raw_sum_dec / iiko_amount)
        else:
            iiko_price = raw_price_dec

        # Расчет суммы строки в iiko
        iiko_sum = quantize_2(iiko_amount * iiko_price)

        # Вычисление погрешности копеек (Pennies rounding delta)
        sum_diff = quantize_2(raw_sum_dec - iiko_sum)

        # Итоговая сумма iiko_sum фиксируется равной raw_sum_dec для точного баланса накладной
        return {
            'iiko_amount': iiko_amount,
            'iiko_price': iiko_price,
            'iiko_sum': raw_sum_dec,
            'sum_diff': sum_diff,
            'packaging_coefficient': coeff_dec
        }
