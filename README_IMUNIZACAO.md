# Módulo de Imunização

Implementa as duas otimizações validadas na planilha:

1. Menor risco da carteira de imunização.
2. Maior convexidade.

Restrições:

- soma dos pesos igual a 100%;
- duration da carteira igual à duration do passivo;
- valor presente dos ativos igual ao valor presente do passivo;
- máximo de títulos configurável;
- limite de concentração configurável.

O módulo enumera combinações de títulos até o limite informado e resolve
cada combinação por programação linear.
