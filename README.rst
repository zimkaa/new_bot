
# стратегия

1 чтение конфигов "storage.json", "state.json"

2 цикл для каждой монеты из storage.json проходит проверку статуса бай или селл

2.1 to_buy 
    2.1.1 Проверяем условие (state) нужно ли чекать следующую свечу (если падение идет то ждем следующую)
        2.1.1.1 Не нужно проверять следующую
            2.1.1.1.1 check_change
                2.1.1.1.1.1 Проверяется сколько времени прошло с момента последней продажи. если больше часа то цена продажи не влияет на условия
                2.1.1.1.1.2 если цены продажи нет значит мы стартовали в первый раз. цена продажи не влияет на условия
                2.1.1.1.1.3 Если падение последней закрытой свечи (номер свечи -2) ниже TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY и
                текущая цена ниже (цены продажи - 1%) то проверяем следующее условие
                    2.1.1.1.1.3.1 Если изменение предыдущей закрытой свечи (номер свечи -3) меньше абсолютного числового значения
                    (изменение цены закрытой свечи (номер свечи -2) + TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY)
                    Тем самым мы убеждаемся что за две свечи у нас толькно есть падение на TRIGGER_PRICE_FALL_PER_MINUTE_FOR_BUY
                    2.1.1.1.1.3.2 Выходим с положительным результатом
                2.1.1.1.1.4 Выходим с отрицательным результатом
                2.1.1.1.1.5 Меняем (state) на True write_state
            2.1.1.1.2 Закончили данный цикл на этом этапе (это значит что ждем минуту для закрытия свечи)
        2.1.1.2 Нужно проверять следующую
            2.1.1.2.1 heck_next_kline
                2.1.1.2.1.1 Если рост цены на 0.1 COEFFICIENT_WAIT_FOR_BUY
                    2.1.1.2.1.1.1 Условие выполнилось выходим и делаем покупку
                2.1.1.2.1.2 Проверяем check_old_kline старые свечи цикл по старым свечам
                    2.1.1.2.1.2.1 Проверям суммарный рост цены на 0.1 COEFFICIENT_WAIT_FOR_BUY
                        2.1.1.2.1.2.1.1 Выходим с положительным результатом
                    2.1.1.2.1.2.2 Прерываем цикл если свеча в минусе
                2.1.1.2.1.2 Выходим с отрицательным результатом
    2.1.2   

2.2 to_sell