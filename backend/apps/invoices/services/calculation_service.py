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
    ) -> dict:
        """
        Вычисляет складские показатели для iiko на основе сырых данных и коэффициента фасовки.
        Устраняет погрешности копеек.
        """
        raw_amount_dec = quantize_3(raw_amount)
        raw_price_dec = quantize_2(raw_price)
        raw_sum_dec = quantize_2(raw_sum)
        coeff_dec = quantize_3(packaging_coefficient or 1.0)

        if coeff_dec <= Decimal('0.000'):
            coeff_dec = Decimal('1.000')

        # 1. Итоговое количество в базовых единицах iiko (кг, л, шт)
        iiko_amount = quantize_3(raw_amount_dec * coeff_dec)

        # 2. Если сумма не была указана явно, рассчитываем ее из raw_amount * raw_price
        if raw_sum_dec == Decimal('0.00') and raw_amount_dec > 0 and raw_price_dec > 0:
            raw_sum_dec = quantize_2(raw_amount_dec * raw_price_dec)

        # 3. Расчет цены за 1 базовую единицу iiko
        if iiko_amount > Decimal('0.000'):
            # Цена за базовую единицу = сырая сумма / итоговое количество в базовых единицах
            iiko_price = quantize_2(raw_sum_dec / iiko_amount)
        else:
            iiko_price = raw_price_dec

        # 4. Расчет суммы строки в iiko
        iiko_sum = quantize_2(iiko_amount * iiko_price)

        # 5. Вычисление погрешности копеек (Pennies rounding delta)
        sum_diff = quantize_2(raw_sum_dec - iiko_sum)

        # Если дельта копеек существует (например +0.01 или -0.02) из-за неделимой дроби,
        # в iiko сумма строки должна совпадать с raw_sum.
        # Поэтому итоговая сумма iiko_sum фиксируется равной raw_sum_dec.
        return {
            'iiko_amount': iiko_amount,
            'iiko_price': iiko_price,
            'iiko_sum': raw_sum_dec,  # Для сохранения точного баланса накладной поставщика
            'sum_diff': sum_diff,
            'packaging_coefficient': coeff_dec
        }
