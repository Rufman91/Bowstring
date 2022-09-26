function Figure = plot_jpk_real_time_oscilloscope_data(Data,MainIndex,XIndex,YIndex1,YIndex2)
% Figure = plot_jpk_real_time_oscilloscope_data(Data,MainIndex,XIndex,YIndex1,YIndex2)

ScaleFactor = 1/10;

X = Data(MainIndex).Channels(:,XIndex);
XLabel = strcat(Data(MainIndex).FancyName{XIndex},' [', Data(MainIndex).UnitName{XIndex},']');
Y1 = Data(MainIndex).Channels(:,YIndex1);
[Multiplier1,Unit1] = AFMImage.parse_unit_scale(range(Y1),...
    Data(MainIndex).UnitName{:,YIndex1},...
    ScaleFactor);
Y1 = Y1.*Multiplier1;
YLabel1 = strcat(Data(MainIndex).FancyName{YIndex1},...
    ' [',...
    Unit1,...
    ']');

Legend{1} = Data(MainIndex).FancyName{YIndex1};

if nargin == 5
    Y2 = Data(MainIndex).Channels(:,YIndex2);
    [Multiplier2,Unit2] = AFMImage.parse_unit_scale(range(Y2),...
        Data(MainIndex).UnitName{:,YIndex2},...
        ScaleFactor);
    Y2 = Y2.*Multiplier2;
    YLabel2 = strcat(Data(MainIndex).FancyName{YIndex2},...
        ' [',...
        Unit2,...
        ']');
    Legend{2} = Data(MainIndex).FancyName{YIndex2};
end

Figure = figure('Color','w');

if nargin == 5
    yyaxis right
    plot(X,Y2)
    ylabel(YLabel2)
end
yyaxis left
plot(X,Y1)
ylabel(YLabel1)

xlabel(XLabel);
legend(Legend);
title(Data(MainIndex).FileName,'Interpreter','none')

end